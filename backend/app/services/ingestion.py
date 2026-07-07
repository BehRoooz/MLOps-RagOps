"""
This module is used to ingest documents into Meilisearch.
"""

from datetime import datetime
from typing import List, Dict, Any
from app.core.clients import meili_client
from app.core.config import settings
from app.core.logging import logger
from app.models.documents import Document
from .chunking import chunk_text
from .embeddings import generate_embeddings


async def ingest_documents(documents: List[Document]) -> Dict[str, Any]:
    """Ingest documents into Meilisearch with chunking + embeddings."""

    doc_index = meili_client.get_index(settings.MEILI_INDEX)
    chunks_index = meili_client.get_index(settings.CHUNKS_INDEX)

    processed_docs, processed_chunks, all_chunk_texts = [], [], []

    for doc in documents:
        # Whole document
        proc_doc = {
            "id": doc.id,
            "text": doc.text,
            "content": doc.text,
            **doc.metadata,
            "indexed_at": datetime.now().isoformat(),
            "chunk_count": 0
        }

        # Chunks
        chunks = chunk_text(doc.text)
        proc_doc["chunk_count"] = len(chunks)
        for i, content in enumerate(chunks):
            chunk_id = f"{doc.id}-chunk-{i}"
            proc_chunk = {
                "id": chunk_id,
                "text": content,
                "content": content,
                "document_id": doc.id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                **doc.metadata,
                "indexed_at": datetime.now().isoformat()
            }
            processed_chunks.append(proc_chunk)
            all_chunk_texts.append(content)

        processed_docs.append(proc_doc)

    # Embeddings
    logger.info(f"Generating embeddings for {len(all_chunk_texts)} chunks...")
    embeddings = await generate_embeddings(all_chunk_texts)

    if len(embeddings) == len(all_chunk_texts):
        for i, chunk in enumerate(processed_chunks):
            chunk["_vectors"] = {"default": embeddings[i]}
    else:
        logger.warning("Embedding mismatch. Adding null vectors.")
        for chunk in processed_chunks:
            chunk["_vectors"] = {"default": None}

    # Insert into Meilisearch
    doc_task = doc_index.add_documents(processed_docs)
    chunk_task = chunks_index.add_documents(processed_chunks) if processed_chunks else None

    return {
        "indexed": len(processed_docs),
        "chunks_created": len(processed_chunks),
        "embeddings_generated": len(embeddings),
        "document_task": doc_task,
        "chunk_task": chunk_task
    }