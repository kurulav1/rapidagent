import pytest
import json

class DummyLLM:
    def __init__(self):
        self.calls = []

    def run(self, provider, model, messages):
        self.calls.append(messages)
        return json.dumps({"type": "final", "content": "done"})

def test_run_react_returns_trace(monkeypatch, llm_registry):
    monkeypatch.setattr(llm_registry, "run", DummyLLM().run)
    trace = llm_registry.run_react("openai", "gpt-4o-mini", "task")
    assert any(step["role"] == "final" for step in trace)
