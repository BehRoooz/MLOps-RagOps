"""
This module is used to search the documents.
"""

from typing import Dict, Any
from fastapi import HTTPException
from app.core.clients import meili_client
from app.core.config import settings
from app.services.embeddings import generate_embeddings
from app.core.logging import logger


async def search_documents(query: str, k: int) -> Dict[str, Any]:
    """Text search on documents index."""
    if not query.strip():
        raise HTTPException(422, "Query cannot be empty")
    index = meili_client.get_index(settings.MEILI_INDEX)
    res = index.search(query, {"limit": k, "attributesToRetrieve": ["*"], "attributesToHighlight": ["text", "content"]})
    return {"hits": res["hits"], "total": res["estimatedTotalHits"], "index_used": "documents", "search_method": "text"}


async def search_chunks(query: str, k: int, use_embeddings: bool = True) -> Dict[str, Any]:
    """Chunk search with optional hybrid (vector+text) mode."""
    if not query.strip():
        raise HTTPException(422, "Query cannot be empty")

    chunks_index = meili_client.get_index(settings.CHUNKS_INDEX)
    search_method = "text"

    if use_embeddings:
        try:
            emb = await generate_embeddings([query])
            if emb:
                query_vec = emb[0]
                if isinstance(query_vec, dict) and "default" in query_vec:
                    query_vec = query_vec["default"]

                res = chunks_index.search(query, {
                    "vector": query_vec,
                    "hybrid": {"semanticRatio": 0.8, "embedder": "default"},
                    "limit": k,
                    "attributesToRetrieve": ["*"]
                })
                search_method = "hybrid"
                return {"hits": res["hits"], "total": res["estimatedTotalHits"], "index_used": "chunks", "search_method": search_method}
        except Exception as e:
            logger.warning(f"Vector search failed: {e}, fallback to text")

    res = chunks_index.search(query, {"limit": k, "attributesToRetrieve": ["*"], "attributesToHighlight": ["text", "content"]})
    return {"hits": res["hits"], "total": res["estimatedTotalHits"], "index_used": "chunks", "search_method": "text"}
