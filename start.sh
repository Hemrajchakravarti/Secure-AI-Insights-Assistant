#!/usr/bin/env bash
# start.sh — starts FastAPI backend and Vite frontend in parallel.
# Press Ctrl+C to stop both.

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACK="$ROOT/backend"
FRONT="$ROOT/frontend"
VENV="$BACK/.venv"
PY="$VENV/bin/python"
UV="$VENV/bin/uvicorn"

# Load .env
if [ -f "$ROOT/.env" ]; then
  export $(grep -v '^#' "$ROOT/.env" | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo ""
  echo "  [ERROR] ANTHROPIC_API_KEY is not set."
  echo "  Create a .env file:  cp .env.example .env  and add your key."
  echo ""
  exit 1
fi

if [ ! -f "$BACK/data/db/insights.db" ]; then
  echo "  [ERROR] Database not found. Run:  python setup.py"
  exit 1
fi

echo ""
echo "  Starting AI Insights Assistant..."
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:5173"
echo "  API docs → http://localhost:8000/docs"
echo "  Press Ctrl+C to stop."
echo ""

# Start backend
cd "$BACK"
PYTHONUTF8=1 \
ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
DB_PATH="$BACK/data/db/insights.db" \
CSV_DIR="$BACK/data/csvs" \
CHROMA_DIR="$BACK/data/db/chroma" \
"$UV" app.main:app --reload --port 8000 &
BACK_PID=$!

# Start frontend
cd "$FRONT"
npm run dev &
FRONT_PID=$!

# Clean shutdown on Ctrl+C
trap "echo '  Shutting down...'; kill $BACK_PID $FRONT_PID 2>/dev/null; exit 0" INT TERM
wait
