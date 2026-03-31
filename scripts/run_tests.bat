@echo off
REM Run pytest tests (HTTP API and WS Server must be running!)
cd /d "%~dp0\.."
set PYTHONPATH=%cd%;%PYTHONPATH%
echo Make sure HTTP API (port 8000) and WS Server (port 8001) are running!
echo.
python -m pytest tests/ -v --tb=short
