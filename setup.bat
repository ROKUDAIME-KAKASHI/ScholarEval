@echo off
echo.
echo ========================================
echo  ScholarEval Setup - Windows
echo ========================================
echo.

REM Check Python installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Setting up environment...
if not exist .env (
    copy .env.example .env
    echo Created .env file
) else (
    echo .env already exists
)

echo.
echo [3/4] Creating data directory...
if not exist data (
    mkdir data
    echo Created data directory
) else (
    echo data directory already exists
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env and add your MISTRAL_API_KEY
echo 2. Run: python main.py
echo 3. Open http://localhost:8000
echo.
pause
