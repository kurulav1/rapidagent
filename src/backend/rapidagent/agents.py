import uuid
from typing import List, Dict, Any
from .llms import LLMRegistry
from .tools import ToolRegistry

class Agent:
    def __init__(self, name: str, model: str, tools: List[str]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.model = model
        self.tools = tools
        self.status = "idle"
        self.trace: List[Dict[str, Any]] = []

class AgentRegistry:
    def __init__(self, llms: LLMRegistry, tools: ToolRegistry):
        self.llms = llms
        self.tools = tools
        self.agents: Dict[str, Agent] = {}

    def list(self, include_trace: bool = False) -> List[Dict[str, Any]]:
        return [
            {
                "id": a.id,
                "name": a.name,
                "model": a.model,
                "tools": a.tools,
                "status": a.status,
                **({"trace": a.trace} if include_trace else {})
            }
            for a in self.agents.values()
        ]

    def create(self, name: str, model: str, tools: List[str]) -> Agent:
        agent = Agent(name, model, tools)
        self.agents[agent.id] = agent
        return agent

    def run(self, agent_id: str, task: str) -> Dict[str, Any]:
        if agent_id not in self.agents:
            raise RuntimeError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]
        agent.status = "running"
        agent.trace = []
        try:
            messages = [
                {"role": "system", "content": "You are a helpful agent. Think step by step."},
                {"role": "user", "content": task},
            ]

            for step in range(3):  # limit steps
                thought = self.llms.run("openai", agent.model, messages)
                agent.trace.append({"step": step + 1, "thought": thought})

                if "use_tool:" in thought:
                    tool_name = thought.split("use_tool:")[1].strip().split()[0]
                    if tool_name not in agent.tools:
                        agent.trace.append({"error": f"Tool {tool_name} not allowed"})
                        break
                    tool = self.tools.get(tool_name)
                    tool_input = thought.split("use_tool:")[1].strip().split(maxsplit=1)[1] if " " in thought else ""
                    result = tool(tool_input)
                    agent.trace.append({"tool": tool_name, "input": tool_input, "output": result})
                    messages.append({"role": "assistant", "content": f"(used {tool_name}, got {result})"})
                else:
                    agent.trace.append({"final": thought})
                    agent.status = "done"
                    return {"result": thought, "trace": agent.trace}

            agent.status = "done"
            return {"result": agent.trace[-1].get("final", ""), "trace": agent.trace}
        except Exception as e:
            agent.status = "error"
            agent.trace.append({"error": str(e)})
            return {"error": str(e), "trace": agent.trace}
def run_stream(self, agent_id: str):
    if agent_id not in self.agents:
        yield {"error": f"Agent {agent_id} not found"}
        return

    agent = self.agents[agent_id]
    agent.status = "running"
    agent.trace = []

    messages = [
        {"role": "system", "content": "You are a helpful agent. Think step by step."},
    ]

    try:
        for step in range(3):
            thought = self.llms.run("openai", agent.model, messages)
            agent.trace.append({"step": step + 1, "thought": thought})
            yield {"type": "thought", "step": step + 1, "content": thought}

            if "use_tool:" in thought:
                tool_name = thought.split("use_tool:")[1].strip().split()[0]
                if tool_name not in agent.tools:
                    error = f"Tool {tool_name} not allowed"
                    agent.trace.append({"error": error})
                    yield {"type": "error", "content": error}
                    break

                tool = self.tools.get(tool_name)
                tool_input = thought.split("use_tool:")[1].strip().split(maxsplit=1)[1] if " " in thought else ""
                result = tool(tool_input)
                agent.trace.append({"tool": tool_name, "input": tool_input, "output": result})
                yield {"type": "tool", "tool": tool_name, "input": tool_input, "output": result}
                messages.append({"role": "assistant", "content": f"(used {tool_name}, got {result})"})
            else:
                agent.trace.append({"final": thought})
                agent.status = "done"
                yield {"type": "final", "content": thought}
                return

        agent.status = "done"
    except Exception as e:
        agent.status = "error"
        agent.trace.append({"error": str(e)})
        yield {"type": "error", "content": str(e)}