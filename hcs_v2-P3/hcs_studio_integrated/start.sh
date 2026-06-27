#!/bin/bash

# HCS Studio Integrated - Startup Script
# Complete Media Processing Suite

echo "========================================"
echo "   HCS Studio Integrated"
echo "   Complete Media Processing Suite"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.8+ first."
    exit 1
fi

echo "[OK] Python3 found"
echo

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[WARNING] Some dependencies may have failed to install."
    echo "The server will try to start with available modules."
fi
echo

# Start the server
echo "Starting HCS Studio Integrated Server..."
echo "Server will be available at: http://localhost:8013"
echo "Press Ctrl+C to stop the server"
echo

python3 server.py

echo
echo "Server stopped."
