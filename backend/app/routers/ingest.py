# -*- coding: utf-8 -*-
"""app/routers/ingest.py"""
import sys, subprocess, logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/run")
async def run_ingestion():
    import os
    base = os.path.join(os.path.dirname(__file__), "../../scripts")
    try:
        for script in ["generate_mock_data.py", "generate_pdfs.py"]:
            r = subprocess.run([sys.executable, os.path.join(base, script)],
                               capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                raise RuntimeError(r.stderr)
        return {"status": "ok", "message": "Re-ingestion complete."}
    except Exception as exc:
        raise HTTPException(500, str(exc))
