import uuid
from typing import List, Dict, Any, Generator
from .llms import LLMRegistry
from .tools import ToolRegistry
from .store import Store

class Agent:
    def __init__(self, agent_id: str, name: str, model: str, tools: List[str], status: str = "idle"):
        self.id = agent_id
        self.name = name
        self.model = model
        self.tools = tools
        self.status = status

class AgentRegistry:
    def __init__(self, store: Store, llms: LLMRegistry, tools: ToolRegistry):
        self.store = store
        self.llms = llms
        self.tools = tools

    def create(self, name: str, model: str, tools: List[str], system_prompt: str | None = None) -> str:
        agent_id = str(uuid.uuid4())
        self.store.create_agent(agent_id, name, model, tools, system_prompt)
        return agent_id

    def get(self, agent_id: str) -> Dict[str, Any] | None:
        agent = self.store.get_agent(agent_id)
        if not agent:
            return None
        agent_tools = self.store.get_agent_tools(agent_id)
        agent_messages = self.store.get_agent_messages(agent_id)
        return {"agent": agent, "tools": agent_tools, "messages": agent_messages}

    def list(self) -> List[Dict[str, Any]]:
        return self.store.list_agents()

    def run_react(self, agent_id: str, task: str) -> Dict[str, Any]:
        agent = self.store.get_agent(agent_id)
        if not agent:
            raise RuntimeError("Agent not found")
        self.store.update_agent_status(agent_id, "running")
        try:
            tools = self.store.get_agent_tools(agent_id)
            trace = self.llms.run_react("openai", agent["model"], task, tools=tools)
            for step in trace:
                role = step.get("role", "assistant")
                content = {k: v for k, v in step.items() if k != "role"}
                self.store.add_trace(agent_id, role, content)
            final = next((s["content"] for s in reversed(trace) if s.get("role") == "final"), "")
            self.store.update_agent_status(agent_id, "idle")
            return {"result": final, "trace": trace}
        except Exception as e:
            self.store.update_agent_status(agent_id, "error")
            raise e

    def run_react_stream(self, agent_id: str, task: str) -> Generator[Dict[str, Any], None, None]:
        agent = self.store.get_agent(agent_id)
        if not agent:
            yield {"type": "error", "content": "Agent not found"}
            return
        self.store.update_agent_status(agent_id, "running")
        try:
            tools = self.store.get_agent_tools(agent_id)
            for step in self.llms.run_react("openai", agent["model"], task, tools=tools):
                role = step.get("role")
                content = {k: v for k, v in step.items() if k != "role"}
                self.store.add_trace(agent_id, role, content)
                if role == "thought":
                    yield {"type": "thought", "content": step.get("content", "")}
                elif role == "action":
                    yield {"type": "action", "tool": step.get("tool"), "input": step.get("input")}
                elif role == "observation":
                    yield {"type": "observation", "tool": step.get("tool"), "output": step.get("output")}
                elif role == "final":
                    yield {"type": "final", "content": step.get("content", "")}
            self.store.update_agent_status(agent_id, "idle")
        except Exception as e:
            self.store.update_agent_status(agent_id, "error")
            yield {"type": "error", "content": str(e)}
