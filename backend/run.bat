@echo off
REM ValueTrack Backend Start Script (Windows)
echo ================================================
echo   ValueTrack - Starting Backend Server
echo ================================================

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Start Flask server
python app.py
