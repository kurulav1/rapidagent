from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from .store import Store
from .llms import LLMRegistry
from .tools import ToolRegistry

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

store = Store("data/rapidagent.db")
tools = ToolRegistry()
llms = LLMRegistry(store, tools)


class ChatRequest(BaseModel):
    provider: str | None = None
    model: str | None = None
    messages: List[Dict[str, str]]


class AgentCreateRequest(BaseModel):
    name: str
    model: str
    tools: List[str] = []
    system_prompt: str | None = None


class ReActRequest(BaseModel):
    provider: str
    model: str
    task: str


class ToolRequest(BaseModel):
    name: str
    input: str


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/providers")
def list_providers():
    return {"providers": llms.list_providers()}


@app.get("/models/{provider}")
def list_models(provider: str):
    return {"models": llms.list_models(provider)}


@app.post("/requests/chat")
def chat(req: ChatRequest):
    if not req.provider or not req.model:
        raise HTTPException(status_code=400, detail="provider and model are required")
    output = llms.run(req.provider, req.model, req.messages)
    return {"messages": req.messages + [{"role": "assistant", "content": output}]}


@app.post("/agents")
def create_agent(req: AgentCreateRequest):
    agent_id = str(uuid4())
    store.create_agent(agent_id, req.name, req.model, req.tools, req.system_prompt)
    return {"id": agent_id}


@app.get("/agents")
def list_agents():
    return {"agents": store.list_agents()}


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    tools = store.get_agent_tools(agent_id)
    messages = store.get_agent_messages(agent_id)
    return {"agent": agent, "tools": tools, "messages": messages}


@app.post("/agents/{agent_id}/chat")
def agent_chat(agent_id: str, req: ChatRequest):
    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    store.update_agent_status(agent_id, "running")
    try:
        tools = store.get_agent_tools(agent_id)
        system_prompt = agent.get("system_prompt")
        history = store.get_agent_messages(agent_id)

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(history)
        all_messages.extend(req.messages)

        if tools:
            trace = llms.run_react("openai", agent["model"], req.messages[-1]["content"], tools=tools)
            for step in trace:
                role = step.get("role", "assistant")
                content = step.get("content", "")
                store.add_trace(agent_id, role, content)
            output = trace[-1]["content"]
        else:
            output = llms.run("openai", agent["model"], all_messages)

        for m in req.messages:
            store.add_agent_message(agent_id, m["role"], m["content"])
        store.add_agent_message(agent_id, "assistant", output)

        store.update_agent_status(agent_id, "idle")
        return {"messages": all_messages + [{"role": "assistant", "content": output}]}
    except Exception as e:
        store.update_agent_status(agent_id, "error")
        raise e


@app.post("/requests/react")
def react(req: ReActRequest):
    trace = llms.run_react(req.provider, req.model, req.task)
    return {"trace": trace}


@app.get("/tools")
def list_tools():
    return {"tools": tools.list()}


@app.post("/tools/run")
def run_tool(req: ToolRequest):
    output = tools.run(req.name, req.input)
    return {"output": output}


@app.get("/agents/{agent_id}/traces")
def get_traces(agent_id: str):
    return {"traces": store.list_traces(agent_id)}
