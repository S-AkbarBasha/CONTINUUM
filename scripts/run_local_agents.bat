@echo off
title CONTINUUM Local Agents Starter
echo ===================================================================
echo   Starting Local Kali (Port 8001) and Parrot (Port 8002) Agents
echo ===================================================================
cd /d "%~dp0\.."

start "CONTINUUM Kali Agent [Port 8001]" cmd /k "python -m uvicorn agents.kali_agent.agent:app --host 0.0.0.0 --port 8001"
start "CONTINUUM Parrot Agent [Port 8002]" cmd /k "python -m uvicorn agents.parrot_agent.agent:app --host 0.0.0.0 --port 8002"

echo Agents launched in separate terminal windows.
echo Kali Agent   : http://127.0.0.1:8001
echo Parrot Agent : http://127.0.0.1:8002
