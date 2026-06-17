@echo off
REM Start TrueVow Financial Management Service
REM Port: 3011 (from .env.local SERVICE_PORT)
REM Requires: Python venv, .env with DATABASE_URL + JWT_SECRET_KEY
echo Starting Financial Management Service on port 3011...
cd /d "%~dp0"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 3011 --reload
