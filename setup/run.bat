@echo off
REM MemScreen Quick Launch Script for Windows

echo.
echo ==========================================
echo   MemScreen v0.6.0 - Quick Launch
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if Ollama is running
echo [INFO] Checking Ollama service...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Ollama service is not running.
    echo Please start Ollama first from the Start Menu
    pause
    exit /b 1
)

REM Launch MemScreen
echo.
echo [INFO] Launching MemScreen v0.6.0...
echo.
python start.py

pause
