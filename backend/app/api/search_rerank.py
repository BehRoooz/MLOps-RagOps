from fastapi import APIRouter, HTTPException
from app.models.rerank import RerankRequest
from app.services.rerank_service import search_with_reranking

router = APIRouter()

@router.post("/search-rerank")
async def search_rerank(req: RerankRequest):
    if not req.query or req.k <= 0:
        raise HTTPException(422, "Invalid query or k")
    res = await search_with_reranking(req)
    return res