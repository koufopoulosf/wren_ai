#!/bin/sh
set -e

echo "Starting Ollama server..."

# Start Ollama server in the background
ollama serve &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Server failed to start within 30 seconds"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Check if model exists
echo "Checking for nomic-embed-text model..."
if ollama list | grep -q "nomic-embed-text"; then
    echo "Model already exists, skipping download"
else
    echo "Model not found, pulling in background..."
    # Pull model in background - don't block startup
    nohup sh -c 'ollama pull nomic-embed-text 2>&1 | tee /tmp/model-pull.log' >/dev/null 2>&1 &
    echo "Model download started in background (check /tmp/model-pull.log for progress)"
fi

# Keep container alive by waiting for the server process
echo "Ollama ready - keeping server running..."
wait $SERVER_PID
