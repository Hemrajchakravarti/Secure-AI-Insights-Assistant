# AI Insights Assistant — Local Setup Guide

AI-powered internal analytics assistant for entertainment data.
Routes queries across SQL, PDF documents, and CSV files using Anthropic tool-calling.

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+   | `node --version` |
| npm    | 9+    | `npm --version` |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) |

---

## Quick start (3 steps)

### Step 1 — Clone and configure

```bash
git clone <repo-url>
cd ai-insights-local

# Copy the env template and add your API key
cp .env.example .env
```

Open `.env` and set:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 2 — Run setup (once)

```bash
python setup.py
```

This will:
- Create `backend/.venv` (Python virtual environment)
- Install all Python packages (`~2 min first run`)
- Generate 6 CSV files + SQLite database with mock entertainment data
- Write 5 internal document texts + ingest them into ChromaDB
  (downloads a ~90 MB sentence-transformer model on first run)
- Install frontend npm packages

### Step 3 — Start the app

**Mac / Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```
start.bat
```

Then open:
- **Frontend UI** → http://localhost:5173
- **API docs**    → http://localhost:8000/docs
- **Health check**→ http://localhost:8000/health

---

## Project structure

```
ai-insights-local/
├── setup.py                  ← Run once to install everything
├── start.sh / start.bat      ← Start both servers
├── .env.example              ← Copy to .env, add API key
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  FastAPI entry point
│   │   ├── routers/
│   │   │   ├── chat.py              POST /api/chat
│   │   │   ├── analytics.py         GET  /api/analytics/*
│   │   │   └── ingest.py            POST /api/ingest/run
│   │   ├── services/
│   │   │   ├── db.py                SQLite (read-only)
│   │   │   └── orchestrator.py      Claude tool-calling loop
│   │   └── tools/
│   │       └── retrieval.py         4 retrieval tool functions
│   ├── scripts/
│   │   ├── generate_mock_data.py    Creates CSVs + SQLite
│   │   └── generate_pdfs.py         Creates doc texts + ChromaDB
│   └── data/                        Auto-created by setup.py
│       ├── csvs/                    6 CSV files
│       ├── pdfs/                    5 document text files
│       └── db/                      insights.db + chroma/
│
└── frontend/
    ├── package.json
    ├── vite.config.js               Proxies /api → localhost:8000
    └── src/
        ├── main.jsx
        ├── App.jsx                  Full UI: chat, charts, trace, history
        └── api/client.js            API helpers
```

---

## The 6 target questions — all answered by the system

| Question | Tools invoked |
|---|---|
| Which titles performed best in 2025? | `query_movie_database` |
| Why is Stellar Run trending? | `search_executive_pdfs` |
| Compare Dark Orbit vs Last Kingdom | `query_movie_database` + `search_executive_pdfs` |
| Which city had strongest engagement last month? | `analyze_csv_data` + `search_executive_pdfs` |
| What explains weak comedy performance? | `query_movie_database` + `search_executive_pdfs` |
| What recommendations for leadership? | `search_executive_pdfs` + `analyze_csv_data` |

---

## Troubleshooting

**"ANTHROPIC_API_KEY is not set"**
→ Make sure `.env` exists in the project root and contains your key.
   The key must start with `sk-ant-`.

**"Database not found"**
→ Run `python setup.py` from the project root.

**Backend starts but charts don't load**
→ The browser console will show a CORS or 502 error.
   Confirm the backend is running: `curl http://localhost:8000/health`

**ChromaDB or sentence-transformers install fails**
→ Make sure you have build tools: on Mac run `xcode-select --install`,
   on Ubuntu run `sudo apt install build-essential`.

**Port already in use**
→ Kill existing processes: `lsof -ti:8000 | xargs kill` (Mac/Linux)
   or change ports in `vite.config.js` and the start script.

**Re-generate all data from scratch**
```bash
rm -rf backend/data
python setup.py
```

---

## Security design (summary)

- **No raw SQL:** The LLM calls named functions that run pre-approved parameterised
  query templates only. No user input ever reaches `execute()` directly.
- **Read-only SQLite:** Opened with `?mode=ro` URI flag — writes are impossible.
- **PII protection:** The system prompt explicitly forbids surfacing individual
  viewer data. All tools return aggregates only.
- **Vector search bounded:** ChromaDB queries capped at 5 results per policy doc.
- **Input validation:** Pydantic enforces max 2000-char messages and role enum.
- **Tool call logging:** Every invocation logged with tool name + input.
