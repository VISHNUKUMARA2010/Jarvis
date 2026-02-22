@echo off
REM Jarvis AI - Run in Background (Headless Mode)
REM Double-click this file to start Jarvis without GUI (voice only)

echo ====================================
echo Starting Jarvis AI in Headless Mode
echo (No GUI - Voice Interface Only)
echo ====================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment Python
    ".venv\Scripts\python.exe" Main.py --headless
) else (
    echo Virtual environment not found, using system Python
    python Main.py --headless
)

echo.
echo Jarvis has stopped.
pause
