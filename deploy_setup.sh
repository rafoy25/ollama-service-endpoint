#!/bin/bash
#
# Production Deployment Setup Script
# Runs ONCE on new server to prepare models
#

set -e  # Exit on error

echo "=========================================="
echo "FastAPI NPU Service - Deployment Setup"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "[1/4] Installing Python dependencies..."
pip3 install -r requirements-npu.txt

# Check for NPU/GPU
echo ""
echo "[2/4] Checking for NPU/iGPU..."
python3 check_npu.py

# Convert model (downloads from HuggingFace)
echo ""
echo "[3/4] Downloading and converting embedding model..."
echo "This will download ~1GB from HuggingFace and convert to OpenVINO..."
if [ -f "models/mxbai-embed-large-ov/model.xml" ]; then
    echo "Model already exists. Skipping conversion."
else
    python3 convert_model_simple.py
fi

# Test embedding service
echo ""
echo "[4/4] Testing NPU embedding service..."
python3 test_npu_embeddings.py

echo ""
echo "=========================================="
echo "✅ Deployment setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start Ollama: docker-compose up -d ollama"
echo "2. Start FastAPI: python3 main.py"
echo "   OR (Docker): docker-compose up -d fastapi"
echo ""
