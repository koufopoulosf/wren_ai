#!/bin/bash
# Initialize Ollama with required embedding model

set -e

echo "🚀 Initializing Ollama with nomic-embed-text model..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done

echo "✅ Ollama is ready!"

# Check if model already exists
if ollama list | grep -q "nomic-embed-text"; then
    echo "✅ nomic-embed-text model already downloaded"
else
    echo "📥 Downloading nomic-embed-text model (~270MB)..."
    ollama pull nomic-embed-text
    echo "✅ Model downloaded successfully!"
fi

echo "🎉 Ollama initialization complete!"
