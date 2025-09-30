import json
import ast
import operator
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Tool(ABC):
    name: str
    description: str
    type: str

    @abstractmethod
    def run(self, input: str) -> Any:
        ...


class CalculatorTool(Tool):
    def __init__(self, name: str = "calculator", description: str = "Perform basic math operations"):
        self.name = name
        self.description = description
        self.type = "calculator"

    def run(self, input: str) -> str:
        try:
            node = ast.parse(input, mode="eval")
            return str(self._eval_node(node.body))
        except Exception as e:
            return f"Error: {e}"

    def _eval_node(self, node: ast.AST) -> Any:
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](self._eval_node(node.operand))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Unsupported expression")


class SearchTool(Tool):
    def __init__(self, name: str = "search", description: str = "Search the web for information"):
        self.name = name
        self.description = description
        self.type = "search"

    def run(self, input: str) -> str:
        return f"Search results for '{input}' (placeholder)"


class TemplateTool(Tool):
    def __init__(self, name: str, description: str, template: str):
        self.name = name
        self.description = description
        self.template = template
        self.type = "template"

    def run(self, input: str) -> str:
        return self.template.replace("{input}", input)


class HttpTool(Tool):
    def __init__(self, name: str, description: str, config: Dict[str, Any]):
        self.name = name
        self.description = description
        self.type = "http"
        self.method = config.get("method", "GET")
        self.url = config.get("url", "")
        self.headers = config.get("headers", {})
        self.body = config.get("body", None)
        self.timeout = float(config.get("timeout", 15))

    def run(self, input: str) -> str:
        import requests

        url = self.url.replace("{input}", input)
        hdrs = {}
        for k, v in self.headers.items():
            hdrs[k] = str(v).replace("{input}", input)

        data = None
        if isinstance(self.body, str):
            data = self.body.replace("{input}", input)
        elif isinstance(self.body, dict):
            data = json.loads(json.dumps(self.body).replace("{input}", input))

        resp = requests.request(
            self.method,
            url,
            headers=hdrs,
            data=data if isinstance(data, str) else None,
            json=data if isinstance(data, dict) else None,
            timeout=self.timeout,
        )

        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            try:
                return json.dumps(resp.json(), ensure_ascii=False)
            except Exception:
                return resp.text
        return resp.text


class PythonCodeTool(Tool):
    def __init__(self, name: str, description: str, config: Dict[str, Any]):
        self.name = name
        self.description = description
        self.type = "python"
        self.code = config.get("code", "")
        self.input_schema = config.get("input_schema", {"type": "string", "description": "Input"})
        self.output_schema = config.get("output_schema", {"type": "string", "description": "Output"})

        local_vars: Dict[str, Any] = {}
        try:
            exec(self.code, {}, local_vars)
        except Exception as e:
            self.fn = None
            self.error = f"Compilation error: {e}"
        else:
            self.fn = local_vars.get("run")
            self.error = None

    def run(self, input: str) -> str:
        if self.error:
            return self.error
        if not callable(self.fn):
            return "Error: run() not defined"
        try:
            return str(self.fn(input))
        except Exception as e:
            return f"Error: {e}"


class ToolRegistry:
    def __init__(self, tools: Optional[List[Tool]] = None):
        self.tools: Dict[str, Tool] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def unregister(self, name: str):
        if name in self.tools:
            del self.tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        result = []
        for t in self.tools.values():
            entry: Dict[str, Any] = {
                "name": t.name,
                "description": t.description,
                "type": t.type,
            }
            if isinstance(t, PythonCodeTool):
                entry["input_schema"] = t.input_schema
                entry["output_schema"] = t.output_schema
            result.append(entry)
        return result

    def run(self, name: str, input: str) -> str:
        tool = self.tools.get(name)
        if not tool:
            return f"Tool {name} not found"
        return str(tool.run(input))

    @staticmethod
    def tool_from_def(defn: Dict[str, Any]) -> Tool:
        t = defn.get("type")
        name = defn.get("name")
        description = defn.get("description", "")
        config = defn.get("config", {}) or {}
        if t == "calculator":
            return CalculatorTool(name=name or "calculator", description=description or "Perform basic math operations")
        if t == "search":
            return SearchTool(name=name or "search", description=description or "Search the web for information")
        if t == "template":
            return TemplateTool(name=name, description=description, template=config.get("template", ""))
        if t == "http":
            return HttpTool(name=name, description=description, config=config)
        if t == "python":
            return PythonCodeTool(name=name, description=description, config=config)
        raise ValueError("Unknown tool type")

    @classmethod
    def from_json_file(cls, path: str, include_defaults: bool = True) -> "ToolRegistry":
        tools: List[Tool] = []
        if include_defaults:
            tools.extend([CalculatorTool(), SearchTool()])
        try:
            with open(path) as f:
                data = json.load(f)
            for d in data:
                tools.append(cls.tool_from_def(d))
        except FileNotFoundError:
            pass
        return cls(tools)
