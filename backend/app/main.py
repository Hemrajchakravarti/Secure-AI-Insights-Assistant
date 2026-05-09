# -*- coding: utf-8 -*-
"""
app/main.py  -  FastAPI entry point.
Loads .env automatically so you can run uvicorn directly from the backend/ folder.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from app/)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, analytics, ingest
from app.services.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s  -  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secure AI Insights Assistant",
    description="Internal analytics assistant  -  Entertainment Co.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Verifying database…")
    init_db()
    logger.info("Ready.")


app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ingest.router,    prefix="/api/ingest",    tags=["Ingest"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "model": os.environ.get("OLLAMA_MODEL","llama3.2"), "ollama_url": os.environ.get("OLLAMA_URL","http://localhost:11434/v1")}
