# -*- coding: utf-8 -*-
"""
scripts/generate_pdfs.py
Writes 5 internal document text files and ingests them into ChromaDB.
Uses sentence-transformers directly (more reliable download than ChromaDB's
built-in DefaultEmbeddingFunction which has a short httpx timeout).
"""

import os
import sys

# Force UTF-8 I/O on Windows
os.environ["PYTHONUTF8"] = "1"

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR    = os.path.join(BASE, "data", "pdfs")
CHROMA_DIR = os.path.join(BASE, "data", "db", "chroma")
os.makedirs(PDF_DIR,    exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

DOCUMENTS = {
    "quarterly_executive_report_Q1_2025.txt": """
QUARTERLY EXECUTIVE REPORT - Q1 2025
ENTERTAINMENT CO. INTERNAL - CONFIDENTIAL

EXECUTIVE SUMMARY
Q1 2025 saw strong performance from Sci-Fi and Drama categories.
Total platform revenue grew 18% YoY to Rs. 1.2B. Subscriber base reached 9.4M.

HIGHLIGHTS
- Stellar Run became our fastest-growing title, driven by social media virality.
  Weekly active viewers grew 240% in the 6 weeks post-launch.
- The Algorithm pre-launch campaign drove record sign-ups: 650K new users in March.
- Comedy genre underperformed budget targets by 34%. Root cause: weak creative
  differentiation and a crowded release window.

OPERATIONAL METRICS
- Content delivery uptime: 99.92%
- Average content load time: 1.4s (down from 1.9s last quarter)
- Top device: Smart TV 38%, Mobile 35%, Web 21%, Tablet 6%

CHALLENGES
- Comedy ROI: Marketing spend on Comic Chaos and Laugh Riot was Rs. 8.5Cr combined,
  generating only Rs. 2.1Cr in incremental subscriptions.
- South India engagement is 28% below national average.
  A targeted localisation strategy is recommended for Q2.

OUTLOOK
Q2 2025 targets: Revenue Rs. 1.4B, Net subscriber additions 800K.
Investment in Korean drama content and regional language dubbing approved.
""",

    "campaign_performance_summary_2025.txt": """
CAMPAIGN PERFORMANCE SUMMARY - 2025 YTD
ENTERTAINMENT CO. MARKETING DIVISION - CONFIDENTIAL

Total marketing spend YTD: Rs. 42.6Cr. Overall ROAS: 3.4x (target: 3.0x).

TITLE-LEVEL PERFORMANCE

Stellar Run
- Spend Rs. 12Cr | Revenue Rs. 51Cr | ROAS 4.25x
- Instagram Reels drove 68% of clicks. Organic search up 190% in April.
- Recommendation: Reduce paid spend; redirect budget to sequel announcement.

Dark Orbit vs Last Kingdom (head-to-head)
- Dark Orbit: Spend Rs. 18Cr | Revenue Rs. 58Cr | ROAS 3.22x | Audience 18-34 urban male
- Last Kingdom: Spend Rs. 9Cr | Revenue Rs. 38Cr | ROAS 4.22x | Audience 25-45 mixed
- Last Kingdom achieved higher efficiency due to strong critical reception.
  31% of viewers upgraded subscription post-watch.
- Dark Orbit wins on raw volume; Last Kingdom wins on customer lifetime value.

Comedy (Laugh Riot + Comic Chaos)
- Combined spend Rs. 8.5Cr | Revenue Rs. 2.1Cr | ROAS 0.25x - BELOW TARGET
- Negative word-of-mouth in first weekend. Exit surveys: predictable plot (52%),
  low production value (38%).
- Recommendation: Pause comedy investment until creative overhaul is complete.

CHANNEL BREAKDOWN (ROAS)
Digital Rs. 18Cr -> 3.6x | OOH Rs. 8Cr -> 2.1x | Influencer Rs. 9Cr -> 5.1x (best)
TV Rs. 5Cr -> 1.8x | Email Rs. 2Cr -> 6.2x (best efficiency)
""",

    "content_roadmap_2025_2026.txt": """
CONTENT ROADMAP - 2025-2026
ENTERTAINMENT CO. CONTENT STRATEGY - CONFIDENTIAL

STRATEGIC DIRECTION
- Sci-Fi budget allocation: increase from 22% to 31% of total content spend.
- Comedy allocation: reduce from 18% to 9% pending creative quality review.
- New pillar: Korean Drama co-productions (target 3 titles by end 2025).

UPCOMING PIPELINE

Q3 2025
- Stellar Run 2 (Sci-Fi) - fast-tracked sequel. Budget Rs. 80Cr. Streaming-exclusive.
- Midnight Protocol (Thriller) - original IP. Budget Rs. 35Cr.
- Bangalore Blues (Drama) - Kannada + Hindi dual launch.

Q4 2025
- Orbital 9 (Sci-Fi) - expanded universe tie-in to The Algorithm.
- Monsoon Wedding Returns (Romance) - OTT + theatrical hybrid.
- First Korean co-production: Silent Storm (Drama).

2026 OUTLOOK
- 4 Sci-Fi originals to consolidate genre leadership.
- Documentary series Cities of India - 8-episode premium docuseries.
- Podcast-to-series adaptation pipeline (2 titles in development).

LOCALISATION STRATEGY
- Tamil, Telugu, Malayalam dubs for all new releases from Q3 2025.
- Regional pricing tiers to be tested in South and East India.
""",

    "policy_guidelines_data_and_ai.txt": """
DATA AND AI POLICY GUIDELINES
ENTERTAINMENT CO. LEGAL & COMPLIANCE - CONFIDENTIAL

1. DATA CLASSIFICATION
  Tier 1 (Public): Press releases, published ratings, platform features.
  Tier 2 (Internal): Viewership aggregates, campaign performance, genre trends.
  Tier 3 (Restricted): Individual viewer PII, financial forecasts, M&A pipeline.

2. AI ACCESS RULES
- AI tools may access Tier 1 and Tier 2 data only.
- Individual viewer PII (Tier 3) must NEVER be surfaced in AI-generated responses.
- All AI tool calls must be logged with timestamp, query intent, and data sources.
- Every AI recommendation must cite the source documents or datasets used.

3. SECURITY CONTROLS
- Database access is read-only at runtime. No writes allowed through AI tools.
- No raw SQL is executed; only parameterised query templates are permitted.
- Vector database queries are bounded: maximum 5 results per similarity search.
- All API endpoints require the ANTHROPIC_API_KEY to be set in the environment.

4. RETENTION
- Viewer PII: retained 24 months post last-active, then anonymised.
- Watch activity logs: retained 36 months for recommendation model training.
- Campaign data: retained 5 years for regulatory compliance.
""",

    "audience_behavior_report_April_2025.txt": """
AUDIENCE BEHAVIOR REPORT - APRIL 2025
ENTERTAINMENT CO. ANALYTICS TEAM - CONFIDENTIAL

ENGAGEMENT OVERVIEW
Monthly Active Users (MAU): 6.8M (up 11% MoM)
Average daily watch time: 48 minutes per user
Content completion rate: 71% (industry benchmark: 65%)

TOP CITIES BY ENGAGEMENT - APRIL 2025
1. Bangalore   - 1.2M sessions | 54 min/day | 76% completion
2. Mumbai      - 1.1M sessions | 51 min/day | 73% completion
3. Hyderabad   - 820K sessions | 49 min/day | 74% completion
4. Delhi       - 780K sessions | 44 min/day | 67% completion
5. Chennai     - 640K sessions | 52 min/day | 78% completion

Bangalore has held the #1 engagement rank for three consecutive months,
driven by a high concentration of 25-34 year-old tech-sector viewers who
skew heavily toward Sci-Fi and Thriller content.

WHY STELLAR RUN IS TRENDING
1. Fan theory virality: The ambiguous ending generated 120K+ posts on Reddit and Twitter.
2. Algorithmic recommendation: Platform surfaces Stellar Run to Sci-Fi completers of The Algorithm.
3. Creator content: 340+ YouTube video essays and reaction videos published in April.
4. Cultural resonance: AI consciousness themes aligned with real-world AI news in March 2025.
5. Celebrity endorsement: Three high-profile endorsements added ~180K incremental streams.

WHY COMEDY IS UNDERPERFORMING
- Average completion rate: 41% (vs 71% platform average)
- Day-7 retention: 12% (vs 34% platform average)
- Exit survey: Predictable (52%), Not funny (38%), Too slow (28%)
- Demographic mismatch: Comedy targeted 18-24 segment, which now prefers Sci-Fi and Action.

LEADERSHIP RECOMMENDATIONS
1. Double down on Sci-Fi - highest engagement and highest LTV genre.
2. Bangalore and Chennai are priority markets - launch regional-language Sci-Fi originals.
3. Pause comedy production until a creative audit is done and a new format tested.
4. Invest in the Smart TV experience - longer sessions, higher completion rates.
5. Use email re-engagement (6.2x ROAS) aggressively for churned subscribers.
"""
}

# ── Write text files ────────────────────────────────────────────────────
print("  Writing document texts...")
for filename, content in DOCUMENTS.items():
    with open(os.path.join(PDF_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"  OK  {filename}")

# ── Load embedding model via sentence-transformers ──────────────────────
# This uses huggingface_hub which has robust retry/resume logic,
# unlike ChromaDB's DefaultEmbeddingFunction which uses httpx with a short timeout.
print("\n  Loading embedding model (sentence-transformers)...")
print("  First run downloads ~90 MB - will resume if interrupted.")

try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Model loaded OK.")
except Exception as e:
    print(f"\n  [ERROR] Failed to load sentence-transformers model: {e}")
    print("  Try: pip install sentence-transformers --upgrade")
    sys.exit(1)

# ── Custom embedding function wrapping sentence-transformers ────────────
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

class STEmbeddingFunction(EmbeddingFunction):
    """Wraps sentence-transformers so ChromaDB uses it instead of its ONNX downloader."""
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = model.encode(list(input), show_progress_bar=False)
        return embeddings.tolist()

# ── Ingest into ChromaDB ────────────────────────────────────────────────
print("\n  Ingesting into ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Delete existing collection so we get a clean re-ingest on re-runs
try:
    client.delete_collection("internal_docs")
except Exception:
    pass

collection = client.create_collection(
    name="internal_docs",
    embedding_function=STEmbeddingFunction(),
    metadata={"hnsw:space": "cosine"},
)

ids, docs, metas = [], [], []
for filename, content in DOCUMENTS.items():
    paras = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 60]
    for i, para in enumerate(paras):
        ids.append(f"{filename}__chunk_{i}")
        docs.append(para)
        metas.append({"source": filename, "chunk": i})

# Ingest in small batches so a slow machine doesn't time out
BATCH = 20
total = len(ids)
for start in range(0, total, BATCH):
    end = min(start + BATCH, total)
    collection.upsert(
        ids=ids[start:end],
        documents=docs[start:end],
        metadatas=metas[start:end],
    )
    print(f"  Ingested {end}/{total} chunks...")

print(f"\n  OK  {total} chunks from {len(DOCUMENTS)} documents ingested.")
print("  ChromaDB ready.")
