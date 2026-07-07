"""
This module is used to search the documents.
"""

from fastapi import APIRouter, HTTPException
from app.models.search import SearchRequest, DirectSearchResult, SearchResponse
from app.services.search_service import search_documents, search_chunks
from app.services.rag_service import rag_search

router = APIRouter()

@router.post("/search-direct", response_model=DirectSearchResult)
async def search_direct(req: SearchRequest):
    if not req.query or req.k <= 0:
        raise HTTPException(422, "Invalid query or k")
    res = await search_documents(req.query, req.k)
    return DirectSearchResult(**res, query=req.query)

@router.post("/search-chunks")
async def search_chunks_route(req: SearchRequest):
    if not req.query or req.k <= 0:
        raise HTTPException(422, "Invalid query or k")
    return await search_chunks(req.query, req.k, req.use_embeddings)

@router.post("/search", response_model=SearchResponse)
async def rag_route(req: SearchRequest):
    if not req.query or req.k <= 0:
        raise HTTPException(422, "Invalid query or k")
    res = await rag_search(req.query, req.k, req.use_embeddings)
    return SearchResponse(**res)
