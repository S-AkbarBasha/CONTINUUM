@echo off
title CONTINUUM Central Controller
echo ===================================================================
echo      CONTINUUM - Intelligent Cross-OS Program Continuity System
echo                      Central Controller
echo ===================================================================
cd /d "%~dp0\.."
echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
