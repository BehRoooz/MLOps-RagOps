#!/usr/bin/env python3
import asyncio
import sys
import os
import sys; sys.path.insert(0, "/app")
import httpx
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings
from app.core.logging import logger
from app.services.rag_service import rag_search

TEST_DOCS = [
    {"id": "Neural Networks", "text": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes called neurons."},
    {"id": "Machine Learning", "text": "Machine learning is a subset of AI that enables systems to learn from data. It includes supervised and unsupervised learning."},
    {"id": "Python Programming", "text": "Python is a high-level programming language known for simplicity. It is widely used in data science and web development."}
]

TEST_CASES = [
    {"question": "What are neural networks?", "ground_truth": "Neural networks are computing systems inspired by biological neural networks."},
    {"question": "What is machine learning?", "ground_truth": "Machine learning is a subset of AI that enables systems to learn from data."}
]

async def ingest_docs():
    logger.info("Ingesting test documents...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post("http://backend:8000/ingest", json=TEST_DOCS)
            if r.status_code == 200:
                logger.info(f"Ingested {len(TEST_DOCS)} documents successfully")
            else:
                logger.error(f"Ingestion failed: {r.status_code} - {r.text}")
        except Exception as e:
            logger.error(f"Error: {e}")
    logger.info("Waiting 10 seconds for Meilisearch to index documents...")
    await asyncio.sleep(10)  # Wait for Meilisearch indexing

async def run_validation():
    logger.info("Running RAGAS validation...")
    llm = ChatOpenAI(base_url=settings.LITELLM_URL, model=settings.LITELLM_MODEL, api_key="dummy")
    emb = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL_NAME, base_url=settings.TEI_EMBEDDINGS_URL, api_key="dummy")
    results = []
    for tc in TEST_CASES:
        try:
            rag_out = await rag_search(query=tc["question"], k=3, use_embeddings=True)
            contexts = [c["content"] for c in rag_out["chunks"]]
            results.append({"question": tc["question"], "answer": rag_out["answer"], "contexts": contexts, "ground_truth": tc["ground_truth"]})
        except Exception as e:
            logger.error(f"Error: {e}")
            results.append({"question": tc["question"], "answer": "Error", "contexts": [], "ground_truth": tc["ground_truth"]})
    data = {k: [r[k] for r in results] for k in results[0].keys()}
    dataset = Dataset.from_dict(data)
    score = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall, context_precision], llm=llm, embeddings=emb, raise_exceptions=False)
    print("\nRAGAS SCORES")
    print(score.to_pandas().to_string())
    avg = score.to_pandas()[["faithfulness", "answer_relevancy", "context_recall", "context_precision"]].mean()
    print("\nAVERAGE SCORES")
    for k, v in avg.items():
        print(f"{k}: {v:.4f}")
    checks = 0
    if all(0 <= avg[k] <= 1 for k in avg.index):
        print("✓ All scores in valid range")
        checks += 1
    if avg["faithfulness"] > 0 or avg["answer_relevancy"] > 0:
        print("✓ Non-zero scores")
        checks += 1
    return checks == 2

async def main():
    await ingest_docs()
    success = await run_validation()
    if success:
        print("\n✓ RAGAS validation successful!")

if __name__ == "__main__":
    asyncio.run(main())
