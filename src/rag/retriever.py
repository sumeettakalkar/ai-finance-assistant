from src.rag.loader import load_documents, chunk_text
from openai import OpenAI
from src.rag.vector_store import VectorStore
import numpy as np
class Retriever:
    def __init__(self):
        self.store = VectorStore()
        self._build_Index()
        
    def _build_Index(self):
        documents = load_documents()
        chunks = []
        for doc in documents:
            new_chunks = chunk_text(doc["text"])
            chunks.extend(new_chunks)
        self.store.build(chunks)
        
    def retrieve(self, query:  str, top_k: int = 5) -> list[str]:
        return self.store.search(query, top_k)
    