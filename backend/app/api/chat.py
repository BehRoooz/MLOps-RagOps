"""
This module is used to chat with the model.
"""
from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest
from app.services.llm_service import generate_chat_completion

router = APIRouter()

@router.post("/chat")
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(422, "Messages cannot be empty")
    try:
        return await generate_chat_completion(req.messages, model=req.model, temperature=req.temperature)
    except Exception:
        raise HTTPException(status_code=502, detail="LLM service unavailable")
