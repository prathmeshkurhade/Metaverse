@echo off
REM Run the HTTP API service on port 8000
cd /d "%~dp0\.."
set PYTHONPATH=%cd%;%PYTHONPATH%
echo Starting HTTP API on port 8000...
echo Swagger docs: http://localhost:8000/docs
cd services\http_api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
