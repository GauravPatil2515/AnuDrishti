@echo off
echo ================================================================
echo DrugTox-AI Enhanced Dashboard - Windows Launcher
echo ================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    echo Download from: https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python detected
echo.

REM Change to dashboard directory
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

REM Check if virtual environment exists
if exist "venv" (
    echo 🐍 Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    call venv\Scripts\activate
    echo ✅ Virtual environment created
)

echo.

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo Trying with --user flag...
    pip install --user -r requirements.txt
)

echo.
echo ================================================================
echo 🚀 Starting DrugTox-AI Enhanced Dashboard
echo ================================================================
echo.
echo 📊 Dashboard will be available at: http://localhost:5000
echo 🔬 API endpoints will be available at: http://localhost:5000/api/
echo.
echo Press Ctrl+C to stop the server
echo ================================================================
echo.

REM Start the Flask application
python app.py

echo.
echo ================================================================
echo Dashboard stopped
echo ================================================================
pause