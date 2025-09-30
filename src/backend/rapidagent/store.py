import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, List

class Store:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                model TEXT,
                status TEXT,
                created_at TEXT,
                last_seen TEXT,
                system_prompt TEXT
            )
        """)
        cur.execute("PRAGMA table_info(agents)")
        cols = [row[1] for row in cur.fetchall()]
        if "system_prompt" not in cols:
            cur.execute("ALTER TABLE agents ADD COLUMN system_prompt TEXT")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_tools (
                agent_id TEXT,
                tool TEXT,
                PRIMARY KEY (agent_id, tool)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                type TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                name TEXT PRIMARY KEY,
                description TEXT,
                type TEXT,
                config TEXT
            )
        """)
        self.conn.commit()

    def get_kv(self, key: str):
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM kv WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def set_kv(self, key: str, value: str):
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def create_agent(self, agent_id: str, name: str, model: str, tools, system_prompt: str | None = None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO agents (id, name, model, status, created_at, last_seen, system_prompt) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agent_id, name, model, "idle", datetime.utcnow().isoformat(), None, system_prompt),
        )
        self.conn.commit()
        self.set_agent_tools(agent_id, tools)
        return agent_id

    def list_agents(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, model, status, created_at, last_seen, system_prompt FROM agents")
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "model": r[2],
                "status": r[3],
                "created_at": r[4],
                "last_seen": r[5],
                "system_prompt": r[6],
            }
            for r in rows
        ]

    def get_agent(self, agent_id: str):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, model, status, created_at, last_seen, system_prompt FROM agents WHERE id=?", (agent_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "model": row[2],
            "status": row[3],
            "created_at": row[4],
            "last_seen": row[5],
            "system_prompt": row[6],
        }

    def update_agent_status(self, agent_id: str, status: str):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE agents SET status=?, last_seen=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), agent_id),
        )
        self.conn.commit()

    def set_agent_system_prompt(self, agent_id: str, prompt: str):
        cur = self.conn.cursor()
        cur.execute("UPDATE agents SET system_prompt=? WHERE id=?", (prompt, agent_id))
        self.conn.commit()

    def set_agent_tools(self, agent_id: str, tools):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM agent_tools WHERE agent_id=?", (agent_id,))
        for t in tools:
            cur.execute("INSERT OR IGNORE INTO agent_tools (agent_id, tool) VALUES (?, ?)", (agent_id, t))
        self.conn.commit()

    def get_agent_tools(self, agent_id: str):
        cur = self.conn.cursor()
        cur.execute("SELECT tool FROM agent_tools WHERE agent_id=?", (agent_id,))
        return [r[0] for r in cur.fetchall()]

    def add_agent_message(self, agent_id: str, role: str, content: str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO agent_messages (agent_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (agent_id, role, content, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def get_agent_messages(self, agent_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT role, content, timestamp FROM agent_messages WHERE agent_id=? ORDER BY id ASC",
            (agent_id,),
        )
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in cur.fetchall()]

    def add_trace(self, agent_id: str, type: str, content: dict | str):
        cur = self.conn.cursor()
        if isinstance(content, dict):
            content = json.dumps(content)
        cur.execute(
            "INSERT INTO traces (agent_id, type, content, timestamp) VALUES (?, ?, ?, ?)",
            (agent_id, type, content, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def list_traces(self, agent_id: str):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT type, content, timestamp FROM traces WHERE agent_id=? ORDER BY id ASC",
            (agent_id,),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            try:
                content = json.loads(r[1])
            except Exception:
                content = r[1]
            result.append({"type": r[0], "content": content, "timestamp": r[2]})
        return result

    def upsert_tool(self, name: str, description: str, type_: str, config: Dict[str, Any] | None):
        cur = self.conn.cursor()
        cfg = json.dumps(config or {})
        cur.execute(
            "INSERT INTO tools (name, description, type, config) VALUES (?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET description=excluded.description, type=excluded.type, config=excluded.config",
            (name, description, type_, cfg),
        )
        self.conn.commit()

    def delete_tool(self, name: str):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tools WHERE name=?", (name,))
        self.conn.commit()

    def list_tools(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT name, description, type, config FROM tools ORDER BY name ASC")
        rows = cur.fetchall()
        result = []
        for r in rows:
            try:
                cfg = json.loads(r[3]) if r[3] else {}
            except Exception:
                cfg = {}
            result.append({"name": r[0], "description": r[1], "type": r[2], "config": cfg})
        return result

    def get_tool(self, name: str) -> Dict[str, Any] | None:
        cur = self.conn.cursor()
        cur.execute("SELECT name, description, type, config FROM tools WHERE name=?", (name,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            cfg = json.loads(r[3]) if r[3] else {}
        except Exception:
            cfg = {}
        return {"name": r[0], "description": r[1], "type": r[2], "config": cfg}
