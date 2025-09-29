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
        max_steps: int = 6,
        tools: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        allowed = tools or []
        tool_list = ", ".join(allowed) if allowed else "none"
        schema = (
            "Respond ONLY as a single-line JSON object per turn using one of these schemas:\n"
            "{\"type\":\"thought\",\"content\":\"...\"}\n"
            "{\"type\":\"action\",\"action\":\"tool_name\",\"input\":\"...\"}\n"
            "{\"type\":\"final\",\"content\":\"...\"}\n"
            f"Allowed tools: {tool_list}."
        )
        system_prompt = (
            "You are a ReAct agent. Think step-by-step. Use tools when helpful. "
            "Follow the JSON schema strictly. Do not include any non-JSON text."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": schema},
            {"role": "user", "content": task},
        ]
        trace: List[Dict[str, Any]] = []

        for _ in range(max_steps):
            output = self.run(provider, model, messages).strip()
            try:
                parsed = json.loads(output)
            except Exception:
                trace.append({"role": "final", "content": output})
                return trace

            t = str(parsed.get("type", "")).lower()

            if t == "thought":
                content = str(parsed.get("content", ""))
                trace.append({"role": "thought", "content": content})
                messages.append({"role": "assistant", "content": output})
                continue

            if t == "action":
                tool_name = str(parsed.get("action", ""))
                tool_input = str(parsed.get("input", ""))
                action_entry = {"tool": tool_name, "input": tool_input}
                if allowed and tool_name not in allowed:
                    observation = f"Error: Tool {tool_name} not allowed."
                    trace.append({"role": "action", **action_entry})
                    trace.append({"role": "observation", "tool": tool_name, "output": observation})
                    messages.append({"role": "assistant", "content": output})
                    messages.append({"role": "system", "content": f"Observation: {observation}"})
                    continue
                result = self.tools.run(tool_name, tool_input)
                trace.append({"role": "action", **action_entry})
                trace.append({"role": "observation", "tool": tool_name, "output": str(result)})
                messages.append({"role": "assistant", "content": output})
                messages.append({"role": "system", "content": f"Observation: {result}"})
                continue

            if t == "final":
                content = str(parsed.get("content", ""))
                trace.append({"role": "final", "content": content})
                return trace

            trace.append({"role": "final", "content": output})
            return trace

        trace.append({"role": "final", "content": ""})
        return trace
