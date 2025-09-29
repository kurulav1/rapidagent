from typing import Dict, Callable, Any, List
import ast
import operator

class Tool:
    def __init__(self, name: str, description: str, run: Callable[[str], str]):
        self.name = name
        self.description = description
        self.run = run

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.register("search", "Search the web for information", self.search)
        self.register("calculator", "Perform basic math operations", self.calculator)

    def register(self, name: str, description: str, fn: Callable[[str], str]):
        self.tools[name] = {"description": description, "run": fn}

    def list(self) -> List[Dict[str, str]]:
        return [{"name": name, "description": data["description"]} for name, data in self.tools.items()]

    def run(self, name: str, input: str) -> str:
        if name not in self.tools:
            return f"Tool {name} not found"
        return str(self.tools[name]["run"](input))

    def search(self, query: str) -> str:
        return f"Search results for '{query}' (placeholder)"

    def calculator(self, expr: str) -> str:
        try:
            node = ast.parse(expr, mode="eval")
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
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Unsupported expression")
