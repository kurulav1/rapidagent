import os
import sqlite3
import json
import uuid
from typing import Any, Dict, List, Optional

class Store:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path

    def connect(self):
        con = sqlite3.connect(self.path)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.row_factory = sqlite3.Row
        return con

    def init(self):
        con = self.connect()
        con.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS tools (name TEXT PRIMARY KEY, description TEXT, schema TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS agents (name TEXT PRIMARY KEY, llm TEXT)")
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(id, text, meta, content='')")
        con.execute("CREATE TABLE IF NOT EXISTS conv (id TEXT PRIMARY KEY, transcript TEXT)")
        con.commit()
        con.close()

    def set_kv(self, k: str, v: str):
        con = self.connect()
        con.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))
        con.commit()
        con.close()

    def get_kv(self, k: str) -> Optional[str]:
        con = self.connect()
        cur = con.execute("SELECT v FROM kv WHERE k=?", (k,))
        row = cur.fetchone()
        con.close()
        return row["v"] if row else None

    def upsert_tool(self, name: str, description: str, schema: Dict[str, Any]):
        con = self.connect()
        con.execute(
            "INSERT INTO tools(name,description,schema) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET description=excluded.description,schema=excluded.schema",
            (name, description, json.dumps(schema)))
        con.commit()
        con.close()

    def list_tools(self) -> List[Dict[str, Any]]:
        con = self.connect()
        cur = con.execute("SELECT name, description, schema FROM tools ORDER BY name")
        rows = [{"name": r["name"], "description": r["description"], "schema": json.loads(r["schema"])} for r in cur.fetchall()]
        con.close()
        return rows

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        con = self.connect()
        cur = con.execute("SELECT name, description, schema FROM tools WHERE name=?", (name,))
        r = cur.fetchone()
        con.close()
        return {"name": r["name"], "description": r["description"], "schema": json.loads(r["schema"])} if r else None

    def upsert_agent(self, name: str, llm: str):
        con = self.connect()
        con.execute("INSERT INTO agents(name,llm) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET llm=excluded.llm", (name, llm))
        con.commit()
        con.close()

    def list_agents(self) -> List[Dict[str, Any]]:
        con = self.connect()
        cur = con.execute("SELECT name,llm FROM agents ORDER BY name")
        rows = [{"name": r["name"], "llm": r["llm"]} for r in cur.fetchall()]
        con.close()
        return rows

    def get_agent_llm(self, name: str) -> Optional[str]:
        con = self.connect()
        cur = con.execute("SELECT llm FROM agents WHERE name=?", (name,))
        r = cur.fetchone()
        con.close()
        return r["llm"] if r else None

    def upsert_doc(self, doc_id: str, text: str, meta: Dict[str, Any]):
        con = self.connect()
        con.execute("INSERT INTO docs(id,text,meta) VALUES(?,?,?)", (doc_id, text, json.dumps(meta)))
        con.commit()
        con.close()

    def search_docs(self, query: str, k: int) -> List[Dict[str, Any]]:
        con = self.connect()
        cur = con.execute("SELECT id, text, meta, rank FROM (SELECT id, text, meta, bm25(docs, 10.0, 1.0) as rank FROM docs WHERE docs MATCH ?) ORDER BY rank LIMIT ?", (query, k))
        rows = [{"id": r["id"], "text": r["text"], "metadata": json.loads(r["meta"])} for r in cur.fetchall()]
        con.close()
        return rows

    def append_conversation(self, transcript: List[Dict[str, str]]):
        con = self.connect()
        cid = self.random_id()
        con.execute("INSERT INTO conv(id, transcript) VALUES(?,?)", (cid, json.dumps(transcript, ensure_ascii=False)))
        con.commit()
        con.close()

    def list_llms(self) -> List[str]:
        return ["openai:gpt-4o-mini", "openai:gpt-4o"]

    def random_id(self) -> str:
        return uuid.uuid4().hex
