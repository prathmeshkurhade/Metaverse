@echo off
REM Run the AI Assistant on port 8002
cd /d "%~dp0\.."
set PYTHONPATH=%cd%;%PYTHONPATH%
echo Starting AI Assistant on port 8002...
echo API docs: http://localhost:8002/docs
cd services\ai_assistant
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
