@echo off
title CONTINUUM Test Suite Runner
echo ===================================================================
echo             Running CONTINUUM Automated Test Suite
echo ===================================================================
cd /d "%~dp0\.."
python -m pytest tests/ -v
pause
