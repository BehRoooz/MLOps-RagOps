"""
This module is used to ingest documents into the system.
"""

from fastapi import APIRouter, HTTPException
from app.models.documents import Document
from app.services.ingestion import ingest_documents

router = APIRouter()

@router.post("/ingest")
async def ingest_route(docs: list[Document]):
    try:
        return await ingest_documents(docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
