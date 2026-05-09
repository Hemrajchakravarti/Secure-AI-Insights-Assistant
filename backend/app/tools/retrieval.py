# -*- coding: utf-8 -*-
"""
app/tools/retrieval.py
Four retrieval tools  -  the only way the AI accesses data.
"""

import os, logging
import pandas as pd
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from app.services.db import get_db

logger     = logging.getLogger(__name__)
CSV_DIR    = os.environ.get("CSV_DIR",    os.path.join(os.path.dirname(__file__), "../../data/csvs"))
CHROMA_DIR = os.environ.get("CHROMA_DIR", os.path.join(os.path.dirname(__file__), "../../data/db/chroma"))

# Lazy-loaded sentence-transformers model (same as used during ingestion)
_st_model = None
def _get_st_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _st_model

class STEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return _get_st_model().encode(list(input), show_progress_bar=False).tolist()

_collection = None
def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_or_create_collection(
            "internal_docs", embedding_function=STEmbeddingFunction())
    return _collection

# ── Pre-approved SQL templates ────────────────────────────────────────────
SQL = {
    "top_titles_by_year": """
        SELECT m.title, m.genre, m.rating,
               COUNT(wa.activity_id) AS watch_count,
               ROUND(AVG(wa.watch_minutes),1) AS avg_watch_mins
        FROM movies m
        LEFT JOIN watch_activity wa ON m.movie_id=wa.movie_id
        WHERE strftime('%Y',wa.watch_date)=?
        GROUP BY m.movie_id ORDER BY watch_count DESC LIMIT 10""",

    "title_detail": """
        SELECT m.title, m.genre, m.rating, m.budget,
               COUNT(wa.activity_id) AS watch_count,
               ROUND(AVG(r.score),2) AS avg_review_score,
               SUM(CASE WHEN wa.completed=1 THEN 1 ELSE 0 END) AS completions
        FROM movies m
        LEFT JOIN watch_activity wa ON m.movie_id=wa.movie_id
        LEFT JOIN reviews r ON m.movie_id=r.movie_id
        WHERE LOWER(m.title) LIKE LOWER(?)
        GROUP BY m.movie_id""",

    "compare_titles": """
        SELECT m.title, m.genre, m.rating,
               COUNT(wa.activity_id) AS watch_count,
               ROUND(AVG(wa.watch_minutes),1) AS avg_watch_mins,
               ROUND(AVG(r.score),2) AS avg_score,
               SUM(CASE WHEN wa.completed=1 THEN 1 ELSE 0 END) AS completions
        FROM movies m
        LEFT JOIN watch_activity wa ON m.movie_id=wa.movie_id
        LEFT JOIN reviews r ON m.movie_id=r.movie_id
        WHERE LOWER(m.title) IN (?,?)
        GROUP BY m.movie_id""",

    "genre_performance": """
        SELECT m.genre,
               COUNT(DISTINCT m.movie_id) AS titles,
               ROUND(AVG(m.rating),2)     AS avg_rating,
               COUNT(wa.activity_id)      AS total_watches,
               ROUND(AVG(wa.watch_minutes),1) AS avg_watch_mins
        FROM movies m
        LEFT JOIN watch_activity wa ON m.movie_id=wa.movie_id
        GROUP BY m.genre ORDER BY total_watches DESC""",
}


def query_movie_database(query_type: str, params: list) -> dict:
    if query_type not in SQL:
        return {"error": f"Unknown query_type: {query_type}", "source": "query_movie_database"}
    logger.info("query_movie_database: %s %s", query_type, params)
    try:
        with get_db() as conn:
            rows = [dict(r) for r in conn.execute(SQL[query_type], params).fetchall()]
        return {"result": rows, "source": "query_movie_database", "query_type": query_type, "row_count": len(rows)}
    except Exception as exc:
        logger.exception("query_movie_database failed")
        return {"error": str(exc), "source": "query_movie_database"}


def search_executive_pdfs(query: str, n_results: int = 4) -> dict:
    logger.info("search_executive_pdfs: %r", query)
    n_results = min(n_results, 5)
    try:
        res = _get_collection().query(query_texts=[query], n_results=n_results,
                                      include=["documents","metadatas","distances"])
        passages = [
            {"text": doc, "source_file": meta.get("source","?"),
             "relevance_score": round(1-dist, 3)}
            for doc, meta, dist in zip(
                res["documents"][0], res["metadatas"][0], res["distances"][0])
        ]
        return {"result": passages, "source": "search_executive_pdfs", "query": query}
    except Exception as exc:
        logger.exception("search_executive_pdfs failed")
        return {"error": str(exc), "source": "search_executive_pdfs"}


def analyze_csv_data(csv_name: str, operation: str, filters: dict = None) -> dict:
    allowed = {"regional_performance","marketing_spend","viewers","watch_activity","reviews"}
    if csv_name not in allowed:
        return {"error": f"CSV not allowed: {csv_name}", "source": "analyze_csv_data"}
    path = os.path.join(CSV_DIR, f"{csv_name}.csv")
    if not os.path.exists(path):
        return {"error": f"File not found: {path}", "source": "analyze_csv_data"}
    logger.info("analyze_csv_data: %s / %s", csv_name, operation)
    try:
        df = pd.read_csv(path)
        if filters:
            for col, val in filters.items():
                if col in df.columns:
                    df = df[df[col].astype(str).str.lower() == str(val).lower()]
        if operation == "top_cities" and "city" in df.columns:
            result = (df.groupby("city")
                      .agg({"views":"sum","avg_watch_pct":"mean","revenue_inr":"sum"})
                      .sort_values("views",ascending=False).head(8).reset_index()
                      .to_dict(orient="records"))
        elif operation == "channel_spend" and "channel" in df.columns:
            result = (df.groupby("channel")
                      .agg({"spend_inr":"sum","impressions":"sum","conversions":"sum"})
                      .reset_index().to_dict(orient="records"))
        elif operation == "platform_breakdown" and "platform" in df.columns:
            result = df["platform"].value_counts().to_dict()
        elif operation == "monthly_trend" and "month" in df.columns:
            result = (df.groupby("month")
                      .agg({"views":"sum","revenue_inr":"sum"})
                      .reset_index().to_dict(orient="records"))
        elif operation == "summary":
            result = df.describe(include="all").fillna("").to_dict()
        else:
            result = df.head(20).to_dict(orient="records")
        return {"result": result, "source": "analyze_csv_data", "csv": csv_name, "operation": operation}
    except Exception as exc:
        logger.exception("analyze_csv_data failed")
        return {"error": str(exc), "source": "analyze_csv_data"}


def calculate_marketing_roi(movie_title: str = None, channel: str = None) -> dict:
    logger.info("calculate_marketing_roi: title=%s channel=%s", movie_title, channel)
    try:
        spend   = pd.read_csv(os.path.join(CSV_DIR, "marketing_spend.csv"))
        movies  = pd.read_csv(os.path.join(CSV_DIR, "movies.csv"))
        merged  = spend.merge(movies[["movie_id","title","genre"]], on="movie_id", how="left")
        if movie_title:
            merged = merged[merged["title"].str.lower().str.contains(movie_title.lower(), na=False)]
        if channel:
            merged = merged[merged["channel"].str.lower() == channel.lower()]
        if merged.empty:
            return {"result": [], "source": "calculate_marketing_roi", "note": "No data matched filters"}
        summary = (merged.groupby(["title","channel"])
                   .agg(total_spend=("spend_inr","sum"),
                        total_impressions=("impressions","sum"),
                        total_conversions=("conversions","sum"))
                   .reset_index())
        summary["cost_per_conversion"] = (summary["total_spend"] / summary["total_conversions"].replace(0,1)).round(0)
        summary["conversion_rate_pct"] = (summary["total_conversions"] / summary["total_impressions"].replace(0,1) * 100).round(3)
        return {"result": summary.to_dict(orient="records"), "source": "calculate_marketing_roi"}
    except Exception as exc:
        logger.exception("calculate_marketing_roi failed")
        return {"error": str(exc), "source": "calculate_marketing_roi"}
