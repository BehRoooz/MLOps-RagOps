import sys
sys.path.insert(0, "/app")
import asyncio
from app.services.rag_service import rag_search

async def test():
    result = await rag_search(query="What are neural networks?", k=3, use_embeddings=True)
    print("Answer:", result["answer"])
    print("Chunks found:", len(result["chunks"]))
    print("Total chunks:", result["total_chunks_found"])
    if result["chunks"]:
        print("First chunk content:", result["chunks"][0]["content"][:100])

asyncio.run(test())
