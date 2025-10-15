#!/bin/bash
# Test script for Docker deployment

echo "=========================================="
echo "Testing Ollama FastAPI Proxy Docker Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}

    echo -n "Testing $name... "
    if [ "$method" == "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi

    if [ "$response" == "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL (HTTP $response)${NC}"
        return 1
    fi
}

echo ""
echo "1. Checking Docker containers..."
docker-compose ps

echo ""
echo "2. Testing API endpoints..."
test_endpoint "Health Check" "http://localhost:8000/api/health"
test_endpoint "List Models" "http://localhost:8000/api/list_models"
test_endpoint "Running Models" "http://localhost:8000/api/running_models"

echo ""
echo "3. Checking pulled models..."
docker exec ollama-proxy ollama list

echo ""
echo "4. Checking GPU access..."
docker exec ollama-proxy nvidia-smi

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
