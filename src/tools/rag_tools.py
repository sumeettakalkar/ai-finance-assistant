"""RAG retrieval tool extracted from the Retriever class.

Provides a simple function interface for retrieving finance context
chunks from the FAISS vector store.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from src.rag.retriever import Retriever


@lru_cache(maxsize=1)
def _retriever() -> Retriever:
    """Lazy singleton so the FAISS index is built only once."""
    return Retriever()


def retrieve_finance_context(query: str, top_k: int = 5) -> List[str]:
    """Retrieve the most relevant finance knowledge chunks for a query.

    Parameters
    ----------
    query : str
        Natural language question to search against the knowledge base.
    top_k : int
        Number of chunks to return (default 5).

    Returns
    -------
    list[str]
        The top matching text chunks from the knowledge base.
    """
    return _retriever().retrieve(query, top_k=top_k)
