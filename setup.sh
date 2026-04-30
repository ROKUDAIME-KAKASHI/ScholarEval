#!/bin/bash

echo ""
echo "========================================"
echo "  ScholarEval Setup - macOS/Linux"
echo "========================================"
echo ""

# Check Python installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "[1/4] Installing dependencies..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "[2/4] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file"
else
    echo ".env already exists"
fi

echo ""
echo "[3/4] Creating data directory..."
if [ ! -d data ]; then
    mkdir -p data
    echo "Created data directory"
else
    echo "data directory already exists"
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your MISTRAL_API_KEY"
echo "2. Run: python3 main.py"
echo "3. Open http://localhost:8000"
echo ""
