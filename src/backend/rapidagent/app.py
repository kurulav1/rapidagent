from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .llms import LLMRegistry
from .tools import ToolRegistry, BuiltinTools
from .rag import RAG
from .store import Store

app = FastAPI(title="RapidAgent")

store = Store("data/rapidagent.db")
store.init()
rag = RAG(store)
tools = ToolRegistry(store)
llms = LLMRegistry(store)
BuiltinTools.install(tools)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    llm: Optional[str] = None
    agent: Optional[str] = None
    messages: List[Message]
    tools: Optional[List[str]] = None
    rag: Optional[Dict[str, Any]] = None
    max_steps: int = 6

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/llms")
def list_llms():
    return {"llms": llms.list(), "default": llms.default()}

@app.post("/llms/set_default")
def set_default_llm(payload: Dict[str, str]):
    name = payload.get("name")
    if not name:
        raise HTTPException(400, "name required")
    llms.set_default(name)
    return {"default": llms.default()}

@app.get("/tools")
def list_tools():
    return {"tools": tools.list()}

@app.post("/tools/register")
def register_tool(payload: Dict[str, Any]):
    tools.register(payload["name"], payload["description"], payload["schema"])
    return {"ok": True}

@app.post("/tools/call")
def call_tool(payload: Dict[str, Any]):
    return {"result": tools.call(payload["name"], payload.get("args", {}))}

@app.get("/agents")
def list_agents():
    return {"agents": store.list_agents()}

@app.post("/agents/create")
def create_agent(payload: Dict[str, str]):
    store.upsert_agent(payload["name"], payload.get("llm") or llms.default())
    return {"ok": True}

@app.post("/rag/docs/upsert")
def upsert_docs(payload: Dict[str, Any]):
    rag.upsert(payload["docs"])
    return {"ok": True}

@app.post("/rag/query")
def query_rag(payload: Dict[str, Any]):
    return {"results": rag.query(payload["query"], payload.get("k", 5))}

@app.post("/requests/chat")
def chat(payload: ChatRequest):
    if payload.rag:
        ctx = rag.query(payload.rag["query"], payload.rag.get("k", 3))
        ctx_text = "\n\n".join([r["text"] for r in ctx])
        payload.messages = payload.messages + [Message(role="system", content=f"RAG context:\n{ctx_text}")]

    target_llm = payload.llm or (store.get_agent_llm(payload.agent) if payload.agent else llms.default())
    if not target_llm:
        raise HTTPException(400, "no llm specified and no default set")

    transcript = [{"role": m.role, "content": m.content} for m in payload.messages]
    step = 0
    while True:
        out = llms.run(target_llm, transcript)
        try:
            maybe = out.strip()
            if maybe.startswith("{") and maybe.endswith("}"):
                as_json = tools.try_parse_json(maybe)
                if "final" in as_json:
                    transcript.append({"role": "assistant", "content": as_json["final"]})
                    break
                if "tool" in as_json:
                    name = as_json["tool"]
                    args = as_json.get("args", {})
                    if payload.tools and name not in payload.tools:
                        transcript.append({"role": "assistant", "content": f"tool {name} not allowed"})
                        break
                    result = tools.call(name, args)
                    transcript.append({"role": "tool", "content": tools.to_json({"name": name, "result": result})})
                else:
                    transcript.append({"role": "assistant", "content": out})
                    break
            else:
                transcript.append({"role": "assistant", "content": out})
                break
        except Exception:
            transcript.append({"role": "assistant", "content": out})
            break
        step += 1
        if step >= payload.max_steps:
            break
    store.append_conversation(transcript)
    return {"messages": transcript}
