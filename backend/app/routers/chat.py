# -*- coding: utf-8 -*-
"""app/routers/chat.py"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.orchestrator import run_agent

logger = logging.getLogger(__name__)
router = APIRouter()

EXAMPLES = [
    "Which titles performed best in 2025?",
    "Why is Stellar Run trending recently?",
    "Compare Dark Orbit vs Last Kingdom",
    "Which city had the strongest engagement last month?",
    "What explains weak comedy performance?",
    "What recommendations would you give for leadership?",
]

class Msg(BaseModel):
    role:    str = Field(..., pattern="^(user|assistant)$")
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[Msg] = Field(default_factory=list)

class TraceItem(BaseModel):
    tool:           str
    input:          dict
    result_summary: str

class ChatResponse(BaseModel):
    answer:     str
    tool_trace: list[TraceItem]
    sources:    list[str]

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info("Chat: %r", req.message[:80])
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        result  = run_agent(req.message, history)
        return ChatResponse(**result)
    except Exception as exc:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/examples")
async def examples():
    return {"examples": EXAMPLES}
