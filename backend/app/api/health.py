"""
This module is used to check the health of the application.
"""

from fastapi import APIRouter
from app.models.health import HealthResponse
from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings import generate_embeddings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        vecs = await generate_embeddings(["test"])
        ok = len(vecs) > 0 and len(vecs[0]) == settings.EMBED_DIM
    except Exception as e:
        logger.warning(f"Health embeddings check failed: {e}")
        ok = False

    return HealthResponse(
        status="healthy",
        embeddings_available=ok,
        embedding_dimensions=settings.EMBED_DIM if ok else None,
    )
