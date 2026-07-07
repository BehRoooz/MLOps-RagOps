"""
This module is used to generate embeddings for the documents.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.core.clients import meili_client
from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings import generate_embeddings

router = APIRouter()

@router.post("/init-index")
async def init_index():
    """Create/Configure Meilisearch indices incl. userProvided vectors."""
    try:
        # documents index
        try:
            doc_idx = meili_client.get_index(settings.MEILI_INDEX)
        except Exception:
            doc_idx = meili_client.create_index(settings.MEILI_INDEX, {"primaryKey": "id"})
        doc_idx.update_searchable_attributes(["text", "title", "content"])
        doc_idx.update_filterable_attributes(["category", "tags", "author", "source"])

        # chunks index
        try:
            chunks_idx = meili_client.get_index(settings.CHUNKS_INDEX)
        except Exception:
            chunks_idx = meili_client.create_index(settings.CHUNKS_INDEX, {"primaryKey": "id"})
        chunks_idx.update_searchable_attributes(["text", "title", "content"])
        chunks_idx.update_filterable_attributes(["document_id", "category", "tags", "chunk_index"])
        chunks_idx.update_settings({
            "embedders": {
                "default": {"source": "userProvided", "dimensions": settings.EMBED_DIM}
            }
        })

        return {
            "message": "Indexes initialized successfully with embeddings support",
            "indexes": [settings.MEILI_INDEX, settings.CHUNKS_INDEX],
            "embedding_dimensions": settings.EMBED_DIM,
        }
    except Exception as e:
        logger.error(f"init-index failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-embeddings")
async def test_embeddings(texts: List[str]):
    try:
        vecs = await generate_embeddings(texts)
        return {
            "input_count": len(texts),
            "embeddings_generated": len(vecs),
            "dimensions": (len(vecs[0]) if vecs else 0),
            "sample_embedding": (vecs[0][:5] if vecs else None),
        }
    except Exception as e:
        logger.error(f"test-embeddings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
