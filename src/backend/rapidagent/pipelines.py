import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from .store import Store
from .tools import ToolRegistry


class PipelineRegistry:
    def __init__(self, store: Store, tools: ToolRegistry):
        self.store = store
        self.tools = tools
        self._init_schema()

    def _init_schema(self):
        cur = self.store.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pipelines (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_steps (
                pipeline_id TEXT,
                step_order INTEGER,
                tool_name TEXT,
                input_mapping TEXT,
                PRIMARY KEY (pipeline_id, step_order)
            )
            """
        )
        self.store.conn.commit()

    def create_pipeline(self, name: str, description: str, steps: List[Dict[str, Any]]) -> str:
        pipeline_id = str(uuid.uuid4())
        cur = self.store.conn.cursor()
        cur.execute(
            "INSERT INTO pipelines (id, name, description, created_at) VALUES (?, ?, ?, ?)",
            (pipeline_id, name, description, datetime.utcnow().isoformat()),
        )
        for idx, step in enumerate(steps):
            cur.execute(
                "INSERT INTO pipeline_steps (pipeline_id, step_order, tool_name, input_mapping) VALUES (?, ?, ?, ?)",
                (pipeline_id, idx, step["tool"], json.dumps(step.get("input_mapping", {}))),
            )
        self.store.conn.commit()
        return pipeline_id

    def list_pipelines(self) -> List[Dict[str, Any]]:
        cur = self.store.conn.cursor()
        cur.execute("SELECT id, name, description, created_at FROM pipelines")
        return [
            {"id": r[0], "name": r[1], "description": r[2], "created_at": r[3]}
            for r in cur.fetchall()
        ]

    def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        cur = self.store.conn.cursor()
        cur.execute(
            "SELECT id, name, description, created_at FROM pipelines WHERE id=?",
            (pipeline_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            "SELECT step_order, tool_name, input_mapping FROM pipeline_steps WHERE pipeline_id=? ORDER BY step_order",
            (pipeline_id,),
        )
        steps = [
            {"order": r[0], "tool": r[1], "input_mapping": json.loads(r[2])}
            for r in cur.fetchall()
        ]
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "steps": steps,
        }

    def run_pipeline(self, pipeline_id: str, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise RuntimeError("Pipeline not found")

        context = dict(initial_input)
        results = []

        for step in pipeline["steps"]:
            tool = self.tools.tools.get(step["tool"])
            if not tool:
                raise RuntimeError(f"Tool {step['tool']} not found")

            mapped_inputs: Dict[str, Any] = {}
            for k, v in step["input_mapping"].items():
                mapped_inputs[k] = context.get(v)

            if tool.type == "python":
                output = tool.run(mapped_inputs)
            else:
                output = tool.run(mapped_inputs.get("input", ""))

            results.append(
                {
                    "step": step["order"],
                    "tool": step["tool"],
                    "input": mapped_inputs,
                    "output": output,
                }
            )

            if isinstance(output, str):
                context[f"step_{step['order']}_output"] = output
            else:
                try:
                    parsed = json.loads(output)
                    if isinstance(parsed, dict):
                        context.update(parsed)
                except Exception:
                    context[f"step_{step['order']}_output"] = output

        return {"pipeline": pipeline_id, "results": results, "final_context": context}
