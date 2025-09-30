import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

from .store import Store
from .tools import ToolRegistry, CalculatorTool, SearchTool
from .llms import LLMRegistry

store = Store("data/rapidagent.db")
tools = ToolRegistry([CalculatorTool(), SearchTool()])
for defn in store.list_tools():
    try:
        tools.register(ToolRegistry.tool_from_def(defn))
    except Exception:
        pass
llms = LLMRegistry(store, tools)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateAgent(BaseModel):
    name: str
    model: str
    tools: list[str] = []
    system_prompt: str | None = None

class ChatRequest(BaseModel):
    messages: list[dict]

class ToolDef(BaseModel):
    name: str
    description: str
    type: str
    config: dict | None = None

@app.get("/models/{provider}")
def list_models(provider: str):
    return {"models": llms.list_models(provider)}

@app.get("/tools")
def list_tools():
    return {"tools": tools.list_tools()}

@app.post("/tools")
def create_tool(defn: ToolDef):
    try:
        store.upsert_tool(defn.name, defn.description, defn.type, defn.config or {})
        tools.register(ToolRegistry.tool_from_def(defn.model_dump()))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/tools/{name}")
def update_tool(name: str, defn: ToolDef):
    existing = store.get_tool(name)
    if not existing:
        raise HTTPException(status_code=404, detail="Tool not found")
    try:
        store.upsert_tool(defn.name, defn.description, defn.type, defn.config or {})
        tools.unregister(name)
        tools.register(ToolRegistry.tool_from_def(defn.model_dump()))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tools/{name}")
def delete_tool(name: str):
    db_tool = store.get_tool(name)
    if not db_tool and name not in tools.tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    store.delete_tool(name)
    tools.unregister(name)
    return {"status": "deleted"}

@app.get("/agents")
def list_agents():
    return {"agents": store.list_agents()}

@app.post("/agents")
def create_agent(req: CreateAgent):
    agent_id = str(uuid.uuid4())
    store.create_agent(agent_id, req.name, req.model, req.tools, req.system_prompt)
    return {"id": agent_id}

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent": agent,
        "tools": store.get_agent_tools(agent_id),
        "messages": store.get_agent_messages(agent_id),
    }

@app.get("/agents/{agent_id}/traces")
def get_traces(agent_id: str):
    return {"traces": store.list_traces(agent_id)}

@app.post("/agents/{agent_id}/chat")
def chat(agent_id: str, req: ChatRequest):
    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Persist user message
    if req.messages:
        last = req.messages[-1]
        store.add_agent_message(agent_id, last["role"], last["content"])

    # Run ReAct loop
    traces = llms.run_react(
        "openai",
        agent["model"],
        req.messages[-1]["content"] if req.messages else "",
        tools=store.get_agent_tools(agent_id),
    )

    # Persist trace steps
    for step in traces:
        role = step.get("role")
        content = {k: v for k, v in step.items() if k != "role"}
        store.add_trace(agent_id, role, content)

    # Persist assistant final reply (if any)
    for step in traces:
        if step["role"] == "final":
            store.add_agent_message(agent_id, "assistant", step["content"])

    return {"traces": traces}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("rapidagent.app:app", host="0.0.0.0", port=8000, reload=True)
