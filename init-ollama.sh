#!/bin/bash
# Ollama initialization script - pulls required models on first startup

set -e

echo "================================================"
echo "Ollama Model Initialization"
echo "================================================"

# Wait for Ollama server to be ready
echo "Waiting for Ollama server to be ready..."
until ollama list > /dev/null 2>&1; do
    echo "  Waiting for Ollama API..."
    sleep 2
done
echo "✓ Ollama server is ready"

# Get models from environment variable or use defaults
MODELS_TO_PULL=${OLLAMA_MODELS:-"gemma3:4b mxbai-embed-large"}

echo ""
echo "Models to pull: $MODELS_TO_PULL"
echo "================================================"

# Convert space-separated string to array
IFS=' ' read -ra MODELS <<< "$MODELS_TO_PULL"

# Pull each model if not already present
for model in "${MODELS[@]}"; do
    echo ""
    echo "Checking model: $model"

    if ollama list | grep -q "$model"; then
        echo "✓ Model '$model' already exists, skipping..."
    else
        echo "⬇ Pulling model: $model (this may take a while...)"
        if ollama pull "$model"; then
            echo "✓ Successfully pulled: $model"
        else
            echo "✗ Failed to pull: $model"
        fi
    fi
done

echo ""
echo "================================================"
echo "✓ Model initialization complete!"
echo "================================================"
echo ""
ollama list
