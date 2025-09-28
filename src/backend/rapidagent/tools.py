from typing import Dict, Callable, Any, List
import requests
import math

class Tool:
    def __init__(self, name: str, description: str, run: Callable[[str], str]):
        self.name = name
        self.description = description
        self.run = run

class ToolRegistry:
    def __init__(self):
        self.tools = {
            "search": {
                "description": "Search the web for information",
                "run": self.search
            },
            "calculator": {
                "description": "Perform basic math operations",
                "run": self.calculator
            }
        }

    def list(self):
        return [{"name": name, "description": data["description"]} for name, data in self.tools.items()]

    def run(self, name: str, input: str) -> str:
        if name not in self.tools:
            return f"Tool {name} not found"
        return self.tools[name]["run"](input)

    def search(self, query: str) -> str:
        return f"Search results for '{query}' (placeholder)"

    def calculator(self, expr: str) -> str:
        try:
            return str(eval(expr, {}, {}))
        except Exception as e:
            return f"Error: {e}"
