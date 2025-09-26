import os
from typing import Dict, Any, List
from openai import OpenAI
from .store import Store

class LLMRegistry:
    def __init__(self, store: Store):
        self.store = store
        if not self.store.get_kv("llm_default"):
            self.store.set_kv("llm_default", "echo")

    def list(self) -> List[str]:
        return ["echo"] + self.store.list_llms()

    def default(self) -> str:
        return self.store.get_kv("llm_default")

    def set_default(self, name: str):
        self.store.set_kv("llm_default", name)

    def run(self, name: str, messages: List[Dict[str, str]]) -> str:
        if name == "echo":
            return messages[-1]["content"]
        if name.startswith("openai:"):
            model = name.split(":", 1)[1]
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set")
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
            return resp.choices[0].message.content or ""
        raise RuntimeError(f"unknown llm {name}")
