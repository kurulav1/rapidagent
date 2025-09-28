import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
from .store import Store
from .tools import ToolRegistry
import json

class LLMRegistry:
    def __init__(self, store: Store, tools: ToolRegistry):
        self.store = store
        self.tools = tools
        if not self.store.get_kv("llm_default"):
            self.store.set_kv("llm_default", "openai:gpt-4o-mini")
        self.providers = {"openai": self._run_openai}

    def list_providers(self) -> List[str]:
        return list(self.providers.keys())

    def list_models(self, provider: str) -> List[str]:
        if provider == "openai":
            return ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        return []

    def run(self, provider: str, model: str, messages: List[Dict[str, str]]) -> str:
        if provider not in self.providers:
            raise RuntimeError(f"Unknown provider {provider}")
        return self.providers[provider](model, messages)

    def _run_openai(self, model: str, messages: List[Dict[str, str]]) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )
        return resp.choices[0].message.content or ""

    def run_react(
        self,
        provider: str,
        model: str,
        task: str,
        max_steps: int = 5,
        tools: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        system_prompt = (
            "You are an intelligent agent. "
            "If a tool is needed, respond ONLY in JSON like {\"action\":\"tool_name\", \"input\":\"...\"}. "
            "Otherwise, respond normally."
        )
        if tools:
            system_prompt += f" Allowed tools: {', '.join(tools)}."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]
        trace: List[Dict[str, str]] = []

        for step in range(max_steps):
            output = self.run(provider, model, messages)
            trace.append({"role": "assistant", "content": output})

            try:
                action = json.loads(output)
                if isinstance(action, dict) and "action" in action and "input" in action:
                    tool_name = action["action"]
                    tool_input = action["input"]
                    if tools and tool_name not in tools:
                        result = f"Error: Tool {tool_name} not allowed."
                    else:
                        result = self.tools.run(tool_name, tool_input)
                    trace.append({"role": "tool", "name": tool_name, "content": result})
                    messages.append({"role": "assistant", "content": output})
                    messages.append({"role": "system", "content": f"Tool {tool_name} returned: {result}"})
                    continue
            except Exception:
                return trace

        return trace
