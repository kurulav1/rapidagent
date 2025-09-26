import json
from typing import Dict, Any, Callable, List
from .store import Store

class ToolRegistry:
    def __init__(self, store: Store):
        self.store = store
        self.functions: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def list(self) -> List[Dict[str, Any]]:
        return self.store.list_tools()

    def register(self, name: str, description: str, schema: Dict[str, Any]):
        self.store.upsert_tool(name, description, schema)

    def bind(self, name: str, fn: Callable[[Dict[str, Any]], Any]):
        self.functions[name] = fn

    def call(self, name: str, args: Dict[str, Any]) -> Any:
        if name in self.functions:
            return self.functions[name](args)
        meta = self.store.get_tool(name)
        if not meta:
            raise RuntimeError(f"unknown tool {name}")
        return {"ok": True, "args": args}

    def try_parse_json(self, s: str) -> Dict[str, Any]:
        return json.loads(s)

    def to_json(self, o: Any) -> str:
        return json.dumps(o, ensure_ascii=False)

class BuiltinTools:
    @staticmethod
    def install(registry: ToolRegistry):
        def add(args):
            return args.get("a", 0) + args.get("b", 0)

        def http_get(args):
            import httpx
            r = httpx.get(args["url"], timeout=10)
            return {"status": r.status_code, "text": r.text[:5000]}

        def rag_search(args):
            from .rag import RAG
            rag = RAG(registry.store)
            k = args.get("k", 3)
            return rag.query(args["query"], k)

        registry.register("add", "add two numbers",
                          {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]})
        registry.bind("add", add)

        registry.register("http_get", "http get",
                          {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]})
        registry.bind("http_get", http_get)

        registry.register("rag_search", "query rag index",
                          {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}}, "required": ["query"]})
        registry.bind("rag_search", rag_search)
