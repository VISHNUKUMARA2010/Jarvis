@echo off
REM Jarvis AI - Run with GUI
REM Double-click this file to start Jarvis with the graphical interface

echo ====================================
echo Starting Jarvis AI with GUI...
echo ====================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment Python
    ".venv\Scripts\python.exe" Main.py
) else (
    echo Virtual environment not found, using system Python
    python Main.py
)

echo.
echo Jarvis has stopped.
pause
