@echo off
cd /d "C:\Users\ASUS\Documents\p-g-e\local\local1\ai-insights-local\backend"
SET PYTHONUTF8=1
SET OLLAMA_MODEL=llama3.2
SET OLLAMA_URL=http://localhost:11434/v1
SET DB_PATH=C:\Users\ASUS\Documents\p-g-e\local\local1\ai-insights-local\backend\data\db\insights.db
SET CSV_DIR=C:\Users\ASUS\Documents\p-g-e\local\local1\ai-insights-local\backend\data\csvs
SET CHROMA_DIR=C:\Users\ASUS\Documents\p-g-e\local\local1\ai-insights-local\backend\data\db\chroma
echo Backend starting on http://localhost:8000 ...
"C:\Users\ASUS\Documents\p-g-e\local\local1\ai-insights-local\backend\.venv\Scripts\uvicorn.exe" app.main:app --reload --port 8000
pause
