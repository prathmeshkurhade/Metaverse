@echo off
REM Run the WebSocket Server on port 8001
cd /d "%~dp0\.."
set PYTHONPATH=%cd%;%PYTHONPATH%
echo Starting WebSocket Server on port 8001...
cd services\ws_server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
