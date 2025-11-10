@echo off
REM Change directory to the script's location
cd /d "%~dp0"

echo ===========================================
echo  Visible–Affinity Integration Tool Launcher
echo ===========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.10+ first.
    pause
    exit /b
)

REM Create a venv if it doesn’t exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate it
call venv\Scripts\activate

REM Install required packages
echo Installing required packages...
pip install --upgrade pip >nul
pip install -r requirements.txt

REM Launch the program
echo.
echo Starting the tool...
python main.py

echo.
pause
