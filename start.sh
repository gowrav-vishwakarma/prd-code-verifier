#!/bin/bash

# PRD Code Verifier Startup Script

echo "🚀 Starting PRD Code Verifier..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your AI provider credentials before running again."
    echo "   For example, set OPENAI_API_KEY=your_key_here"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    uv sync
fi

# Start the application
echo "🌐 Starting web server..."
echo "   Open your browser to: http://localhost:8000"
echo "   Press Ctrl+C to stop the server"
echo ""

uv run main.py
