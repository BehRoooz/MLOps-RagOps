"""
This module is used to evaluate the RAGAS model.
"""
import asyncio
from typing import List, Dict, Any

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)

from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.services.rag_service import rag_search


# --- 1. Configure LLM and Embeddings for RAGAS ---

ragas_llm = ChatOpenAI(
    base_url=settings.LITELLM_URL,
    model=settings.LITELLM_MODEL,
    api_key="dummy"
)

ragas_embeddings = OpenAIEmbeddings(
    model=settings.EMBEDDING_MODEL_NAME,
    base_url=settings.TEI_EMBEDDINGS_URL,
    api_key="dummy"
)


# --- 2. Evaluation Logic ---
async def run_evaluation(testset: List[Dict[str, Any]]):
    logger.info("Starting Ragas evaluation...")

    results = []
    for item in testset:
        question = item['question']
        logger.info(f"Processing question: {question}")
        try:
            rag_output = await rag_search(query=question, k=3, use_embeddings=True)
            contexts = [c['content'] for c in rag_output['chunks']]
            results.append({
                'question': question,
                'answer': rag_output['answer'],
                'contexts': contexts,
                'ground_truth': item['ground_truth']
            })
        except Exception as e:
            logger.error(f"RAG execution failed for question '{question}': {e}")
            results.append({
                'question': question,
                'answer': "Error during RAG execution.",
                'contexts': [],
                'ground_truth': item['ground_truth']
            })
            continue

    data = {k: [r[k] for r in results] for k in results[0].keys()}
    dataset = Dataset.from_dict(data)

    score = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        raise_exceptions=False
    )

    logger.info("Ragas Evaluation Complete.")
    print(score)
    return score.to_pandas()


if __name__ == "__main__":
    example_testset = [
        {
            "question": "Define autoencoders",
            "ground_truth": "Autoencoders are a type of neural network used for learning efficient data codings in an unsupervised manner."
        },
        {
            "question": "What is the primary goal of linear factor models?",
            "ground_truth": "The primary goal of linear factor models, such as PCA, is to model the covariance structure among variables by a few latent factors."
        }
    ]
    asyncio.run(run_evaluation(example_testset))