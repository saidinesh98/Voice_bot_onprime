#!/bin/bash

# Start Ollama in the background
/bin/ollama serve &

# Wait for Ollama to become ready
echo "⏳ Waiting for Ollama server to start..."
while ! ollama list > /dev/null 2>&1; do
    sleep 1
done

# Pull the requested model
echo "📥 Pulling model: llama3.2:1b"
ollama pull llama3.2:1b

echo "✅ Model ready. Keeping process alive..."
# Wait for the background process
wait
