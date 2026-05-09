# -*- coding: utf-8 -*-
"""app/routers/analytics.py"""
import logging
from fastapi import APIRouter, HTTPException
from app.tools.retrieval import query_movie_database, analyze_csv_data

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/genre-performance")
async def genre_performance():
    r = query_movie_database("genre_performance", [])
    if "error" in r: raise HTTPException(500, r["error"])
    return r

@router.get("/top-titles")
async def top_titles(year: str = "2025"):
    r = query_movie_database("top_titles_by_year", [year])
    if "error" in r: raise HTTPException(500, r["error"])
    return r

@router.get("/regional-engagement")
async def regional_engagement():
    r = analyze_csv_data("regional_performance", "top_cities")
    if "error" in r: raise HTTPException(500, r["error"])
    return r

@router.get("/marketing-channels")
async def marketing_channels():
    r = analyze_csv_data("marketing_spend", "channel_spend")
    if "error" in r: raise HTTPException(500, r["error"])
    return r

@router.get("/platform-breakdown")
async def platform_breakdown():
    r = analyze_csv_data("viewers", "platform_breakdown")
    if "error" in r: raise HTTPException(500, r["error"])
    return r
