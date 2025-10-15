# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a FastAPI-based proxy service for Ollama (local LLM runtime). The service provides REST API endpoints to interact with Ollama models for chat/prompts and embeddings generation, with CORS support for web clients.

## Architecture

### Deployment Modes

**Local Development**: FastAPI connects to Ollama at `http://localhost:11434`
**Docker Production**: FastAPI connects to Ollama at `http://ollama:11434` (Docker service DNS)

The Ollama URL is configurable via `OLLAMA_URL` environment variable.

### Main Service ([main.py](main.py))
- FastAPI application acting as a reverse proxy to Ollama
- Uses `httpx` for async HTTP requests to Ollama backend
- Uses `requests` for synchronous operations (model listing)
- Implements CORS middleware with permissive settings (`allow_origins: ["*"]`)
- Default embedding models: `mxbai-embed-large`, `nomic-embed-text`, `all-minilm`

### Docker Architecture
- **Network**: Custom bridge network `ollama-network` for inter-container communication
- **Ollama Container**: Runs with NVIDIA GPU access, exposes port 11434
- **FastAPI Container**: Python 3.10, depends on Ollama health check, exposes port 8000
- **Volume**: `ollama-data` for persistent model storage
- **Health Checks**: Both services have health checks for orchestration

### API Endpoints
- `GET /api/health` - Health check endpoint
- `GET /api/list_models` - Lists all available Ollama models (via `/api/tags`)
- `GET /api/running_models` - Shows currently running models (via `/api/ps`)
- `POST /api/prompts` - Generate text completions (proxies to `/api/generate`)
- `POST /api/embeddings` - Generate text embeddings (proxies to `/api/embed`)

### Test Service ([test.py](test.py))
Separate FastAPI application for testing concurrency and CPU-intensive tasks:
- PostgreSQL integration (database: `brokentooth`)
- `ProcessPoolExecutor` for CPU-bound tasks (prime number computation)
- Runs on port 5000

### Load Testing
- **[locustfile.py](locustfile.py)**: Comprehensive load test scenarios
  - `FastAPIUser`: Mixed workload (weighted tasks)
  - `HeavyUser`: Concurrent embedding + chat requests
  - `ChatOnlyUser`: Chat-only traffic (weight: 3)
  - `EmbeddingOnlyUser`: Embedding-only traffic (weight: 1)
- **[run_load_test.py](run_load_test.py)**: Launcher script for Locust web UI

## Development Commands

### Running Locally (Development)

#### Main Service
```bash
python main.py
# Runs on http://0.0.0.0:8000 with auto-reload
# Requires Ollama running locally on port 11434
```

#### Test Service
```bash
python test.py
# Runs on http://0.0.0.0:5000 with auto-reload
```

#### Load Testing
```bash
# Install dependencies
pip install -r requirements-locust.txt

# Start the FastAPI server first
python main.py

# Run load tests (opens web UI at http://localhost:8089)
python run_load_test.py
```

### Running with Docker (Production)

#### Prerequisites
- Docker installed
- Docker Compose V2+ installed
- NVIDIA Container Toolkit installed (for GPU support - see [ollama-gpu-guide.md](ollama-gpu-guide.md))
- NVIDIA GPU drivers properly configured

#### Quick Start
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (caution: deletes model data)
docker-compose down -v
```

#### Verify GPU Access
```bash
# Check Ollama has GPU access
docker exec ollama nvidia-smi

# Pull and run a model in Ollama
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama run llama3
```

#### Service URLs
- **FastAPI**: `http://localhost:8000` (exposed to host)
- **Ollama**: `http://localhost:11434` (exposed for debugging)
- **Internal Communication**: FastAPI → Ollama via `http://ollama:11434` (Docker DNS)

#### Common Docker Commands
```bash
# Rebuild after code changes
docker-compose up -d --build

# View service status
docker-compose ps

# Check container logs
docker-compose logs ollama
docker-compose logs fastapi

# Restart specific service
docker-compose restart fastapi

# Access container shell
docker exec -it fastapi-proxy bash
docker exec -it ollama bash
```

## Dependencies

Main service requires:
- `fastapi`
- `httpx` (async HTTP client)
- `requests` (sync HTTP client)
- `pydantic`
- `uvicorn`

Load testing requires:
- `locust==2.17.0`
- `requests==2.31.0`

Test service additionally requires:
- `psycopg2` (PostgreSQL adapter)

## Ollama Integration

The service expects Ollama to be running locally. See [ollama-gpu-guide.md](ollama-gpu-guide.md) for detailed Docker/GPU setup instructions including:
- NVIDIA GPU setup with Docker
- NVIDIA Container Toolkit installation
- Running Ollama container with GPU access
- AMD ROCm support for AMD GPUs

## Connecting External Containers (e.g., RAGFlow)

External containers can connect to this service via the `ollama-network`:

### Option 1: Join Existing Network (Recommended)
```yaml
# In your external service's docker-compose.yml
services:
  ragflow:
    image: your-ragflow-image
    networks:
      - ollama-network

networks:
  ollama-network:
    external: true
```

Then access FastAPI at: `http://fastapi-proxy:8000`

### Option 2: Host Network Access
Access FastAPI from any container via host: `http://host.docker.internal:8000` (Docker Desktop) or `http://<host-ip>:8000` (Linux)

### Testing External Connectivity
```bash
# From within any container on ollama-network
curl http://fastapi-proxy:8000/api/health

# From host
curl http://localhost:8000/api/health
```

## Error Handling Patterns

All endpoints follow similar error handling:
1. Check for `"error"` key in Ollama response JSON
2. Raise `HTTPException` with status 404 if error found
3. Catch `httpx.HTTPStatusError` / `httpx.RequestError`
4. Catch `requests.HTTPError` / `requests.RequestException`
5. Return 500 status for connection errors

## Timeout Configuration

- Prompt generation: 60s timeout (configurable in [main.py](main.py:98))
- Embeddings: 60s timeout (configurable in [main.py](main.py:77))
- Load test prompts: 60s timeout
- Load test embeddings: 30s timeout

## Important Notes

### Request/Response Models
- `PromptsRequest`: Pydantic model for chat/completion requests (model, prompt, stream flag)
- `EmbeddingsRequest`: Pydantic model for embedding requests (model, input list)
- Default chat model: `llama3`
- Default embedding model: `mxbai-embed-large` (first in `embedding_models` list)

### HTTP Client Usage Pattern
- `httpx.AsyncClient`: Used for async POST requests (prompts, embeddings)
- `requests`: Used for sync GET requests (list_models, running_models)
- All Ollama responses are checked for `"error"` key before returning

### Error Response Codes
- 400: Ollama returned an error in response JSON
- 404: Model not found or error from model service
- 500: Connection error or request failure
