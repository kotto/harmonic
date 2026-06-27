#!/bin/bash

# HCS Harmonic Music Generator - Start Script (Linux/macOS)

echo "🎵 HCS Harmonic Music Generator Starting..."
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p templates
mkdir -p static
mkdir -p generated_music

# Start server
echo "🚀 Starting server..."
echo "🌐 Web Interface: http://localhost:8020"
echo "📊 API Documentation: http://localhost:8020/docs"
echo "=========================================="

python3 server.py
