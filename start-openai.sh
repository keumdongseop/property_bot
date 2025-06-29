#!/bin/bash

# ThermoEngine Web Starter Script for OpenAI

echo "Starting ThermoEngine Web Interface with ChatGPT..."

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    echo "Please set it with: export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install Python dependencies
source venv/bin/activate
if ! python -c "import numpy" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r mcp-server/requirements.txt
fi

# Install Node.js dependencies if needed
if [ ! -d "backend/node_modules" ]; then
    echo "Installing Node.js dependencies..."
    cd backend && npm install && cd ..
fi

# Start the server
echo "Starting server on http://localhost:3001"
cd backend && node server-openai.js