@echo off
setlocal EnableDelayedExpansion

SET ROOT=%~dp0
IF "%ROOT:~-1%"=="\" SET ROOT=%ROOT:~0,-1%

SET BACK=%ROOT%\backend
SET FRONT=%ROOT%\frontend
SET VENV=%BACK%\.venv
SET VENV_PY=%VENV%\Scripts\python.exe
SET ENV_FILE=%ROOT%\.env

IF NOT EXIST "%VENV_PY%" (
  echo [ERROR] Virtual environment not found. Run: python setup.py
  pause & exit /b 1
)
IF NOT EXIST "%BACK%\data\db\insights.db" (
  echo [ERROR] Database not found. Run: python setup.py
  pause & exit /b 1
)

REM Load optional .env settings
SET OLLAMA_MODEL=llama3.2
SET OLLAMA_URL=http://localhost:11434/v1
IF EXIST "%ENV_FILE%" (
  FOR /f "usebackq eol=# tokens=1,* delims==" %%A IN ("%ENV_FILE%") DO (
    IF "%%A"=="OLLAMA_MODEL" SET OLLAMA_MODEL=%%B
    IF "%%A"=="OLLAMA_URL"   SET OLLAMA_URL=%%B
  )
)

REM Check Ollama is running using PowerShell (works on all Windows versions)
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 3; exit 0 } catch { exit 1 }" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo.
  echo   [ERROR] Ollama is not running or not reachable.
  echo.
  echo   Fix: Open a NEW terminal and run:
  echo        ollama serve
  echo   Wait for "Ollama is running" message, then run start.bat again.
  echo.
  echo   Or: Open the Ollama desktop app from your system tray.
  echo.
  pause & exit /b 1
)

echo   Ollama is running. Model: %OLLAMA_MODEL%

SET BACK_SCRIPT=%ROOT%\_run_backend.bat
(
  echo @echo off
  echo cd /d "%BACK%"
  echo SET PYTHONUTF8=1
  echo SET OLLAMA_MODEL=%OLLAMA_MODEL%
  echo SET OLLAMA_URL=%OLLAMA_URL%
  echo SET DB_PATH=%BACK%\data\db\insights.db
  echo SET CSV_DIR=%BACK%\data\csvs
  echo SET CHROMA_DIR=%BACK%\data\db\chroma
  echo echo Backend starting on http://localhost:8000 ...
  echo "%VENV%\Scripts\uvicorn.exe" app.main:app --reload --port 8000
  echo pause
) > "%BACK_SCRIPT%"

SET FRONT_SCRIPT=%ROOT%\_run_frontend.bat
(
  echo @echo off
  echo cd /d "%FRONT%"
  echo echo Frontend starting on http://localhost:5173 ...
  echo npm run dev
  echo pause
) > "%FRONT_SCRIPT%"

echo.
echo   Starting AI Insights Assistant  [Ollama - free and local]
echo   Model:    %OLLAMA_MODEL%
echo   Backend   --^>  http://localhost:8000
echo   Frontend  --^>  http://localhost:5173
echo.

start "AI Insights - Backend" cmd /k "%BACK_SCRIPT%"
timeout /t 2 /nobreak >nul
start "AI Insights - Frontend" cmd /k "%FRONT_SCRIPT%"

echo   Two windows opened. Open http://localhost:5173 in your browser.
echo.
endlocal