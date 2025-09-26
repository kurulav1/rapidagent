from typing import List, Dict, Any
from .store import Store

class RAG:
    def __init__(self, store: Store):
        self.store = store

    def upsert(self, docs: List[Dict[str, Any]]):
        for d in docs:
            doc_id = str(d.get("id") or self.store.random_id())
            text = str(d.get("text", ""))
            meta = d.get("metadata") or {}
            self.store.upsert_doc(doc_id, text, meta)

    def query(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return self.store.search_docs(query, k)
