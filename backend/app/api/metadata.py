"""
This module is used to upload and get metadata for documents.

It uses the Minio client to upload files to the Minio server.
It uses the database to store the metadata for the documents.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.minio_client import upload_file
from app.services.db import insert_document_metadata, get_document_metadata

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    minio_path = upload_file(file.filename, content)
    document_id = insert_document_metadata(
        filename=file.filename,
        minio_path=minio_path,
        chunk_count=0,
        embedding_model=None,
    )
    return {"document_id": document_id, "filename": file.filename, "minio_path": minio_path}

@router.get("/metadata/{document_id}")
async def get_metadata(document_id: int):
    record = get_document_metadata(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return record