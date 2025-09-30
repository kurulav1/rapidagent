import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os, json

from .store import Store
from .tools import ToolRegistry
from .llms import LLMRegistry

store = Store("data/rapidagent.db")
tools = ToolRegistry.from_json_file("data/tools.json", include_defaults=True)
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

class PipelineStep(BaseModel):
    tool: str
    input_mapping: dict

class PipelineDef(BaseModel):
    name: str
    description: str | None = None
    steps: list[PipelineStep]

PIPELINE_FILE = "data/pipelines.json"

def load_pipelines():
    try:
        with open(PIPELINE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_pipelines(pipelines):
    os.makedirs("data", exist_ok=True)
    with open(PIPELINE_FILE, "w") as f:
        json.dump(pipelines, f, indent=2)


@app.get("/models/{provider}")
def list_models(provider: str):
    return {"models": llms.list_models(provider)}


@app.get("/tools")
def list_tools():
    return {"tools": tools.list_tools()}


@app.post("/tools")
def create_tool(defn: ToolDef):
    try:
        tool = tools.tool_from_def(defn.dict())
        tools.register(tool)

        path = "data/tools.json"
        os.makedirs("data", exist_ok=True)
        try:
            with open(path) as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        data = [d for d in data if d.get("name") != defn.name]
        data.append(defn.dict())
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/tools/{tool_name}")
def delete_tool(tool_name: str):
    if tool_name not in tools.tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    tools.unregister(tool_name)

    path = "data/tools.json"
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    data = [d for d in data if d.get("name") != tool_name]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "deleted"}


@app.get("/pipelines")
def list_pipelines():
    return {"pipelines": load_pipelines()}


@app.post("/pipelines")
def create_pipeline(defn: PipelineDef):
    pipelines = load_pipelines()
    pipeline_id = str(uuid.uuid4())
    pipeline = {
        "id": pipeline_id,
        "name": defn.name,
        "description": defn.description or "",
        "steps": [s.dict() for s in defn.steps],
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    }
    pipelines.append(pipeline)
    save_pipelines(pipelines)
    return {"id": pipeline_id}


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

    if req.messages:
        last = req.messages[-1]
        store.add_agent_message(agent_id, last["role"], last["content"])

    traces = llms.run_react(
        "openai",
        agent["model"],
        req.messages[-1]["content"] if req.messages else "",
        tools=store.get_agent_tools(agent_id),
    )

    for step in traces:
        if step["role"] == "final":
            store.add_agent_message(agent_id, "assistant", step["content"])

    return {"traces": traces}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("rapidagent.app:app", host="0.0.0.0", port=8000, reload=True)
