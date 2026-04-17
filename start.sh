#!/bin/bash
# start.sh - Start the VM server

echo "🚀 Starting Voice Bot Server..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 5
fi

# Check if model exists
if ! ollama list | grep -q llama3.2:3b; then
    echo "Downloading model..."
    ollama pull llama3.2:3b
fi

# Activate virtual environment
source venv/bin/activate

# Start the server
python server.py