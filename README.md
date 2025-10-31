# Ollama FastAPI Proxy

A FastAPI-based reverse proxy for Ollama with Docker support, GPU acceleration, and automatic model initialization.

## Features

- 🚀 FastAPI REST API for Ollama
- 🎮 NVIDIA GPU support via Docker
- 🤖 Automatic model pulling on startup
- 🔄 Hot-reload for development
- 🌐 CORS-enabled for web clients
- 📦 Fully containerized with Docker Compose
- 🔌 Ready for external service integration (e.g., RAGFlow)

## Quick Start

### Prerequisites

- Docker & Docker Compose V2+
- NVIDIA GPU drivers
- NVIDIA Container Toolkit ([Setup Guide](ollama-gpu-guide.md))

### 1. Start Services

```bash
# Start all services (Ollama + FastAPI + Model Initialization)
docker-compose up -d

# Watch the logs (model pulling may take 5-15 minutes)
docker-compose logs -f ollama-init
```

### 2. Verify Setup

```bash
# Check service status
docker-compose ps

# List available models
curl http://localhost:8000/api/list_models

# Test chat completion
curl -X POST http://localhost:8000/api/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

## Configuration

### Custom Models

Create a `.env` file to specify which models to pull:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and set your models
OLLAMA_MODELS=llama3 mistral codellama mxbai-embed-large
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Default Models

If no `.env` file is provided, these models are pulled automatically:
- `llama3` - Chat/completion model
- `mxbai-embed-large` - Embedding model
- `nomic-embed-text` - Embedding model
- `all-minilm` - Lightweight embedding model

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/list_models` | GET | List available models |
| `/api/running_models` | GET | Show running models |
| `/api/prompts` | POST | Generate text completion |
| `/api/embeddings` | POST | Generate embeddings |

### Example Requests

#### Generate Text
```bash
curl -X POST http://localhost:8000/api/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Explain quantum computing in simple terms",
    "stream": false
  }'
```

#### Generate Embeddings
```bash
curl -X POST http://localhost:8000/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mxbai-embed-large",
    "input": ["Hello world", "How are you?"]
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│           ollama-network (Bridge)               │
│                                                 │
│  ┌──────────────┐         ┌─────────────────┐  │
│  │   Ollama     │ ◄─────► │   FastAPI       │  │
│  │              │         │                 │  │
│  │  GPU: ✓      │         │  Port: 8000     │  │
│  │  Port: 11434 │         │                 │  │
│  └──────────────┘         └─────────────────┘  │
│         ▲                          ▲            │
│         │                          │            │
│         │     ┌────────────────┐   │            │
│         └─────┤  ollama-init   │   │            │
│               │ (one-time run) │   │            │
│               └────────────────┘   │            │
└────────────────────────────────────┼────────────┘
                                     │
                              localhost:8000
```

## Connecting External Services

### RAGFlow or Other Containers

Add to your external service's `docker-compose.yml`:

```yaml
services:
  your-service:
    image: your-image:latest
    networks:
      - ollama-network
    environment:
      - LLM_API_URL=http://fastapi-proxy:8000

networks:
  ollama-network:
    external: true
```

## Management

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f ollama
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart fastapi
```

### Stop Services
```bash
# Stop (keeps data)
docker-compose down

# Stop and remove volumes (deletes models)
docker-compose down -v
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Manually Pull Models
```bash
docker exec -it ollama-proxy ollama pull <model-name>
docker exec -it ollama-proxy ollama list
```

## Troubleshooting

### Models Not Loading

Check initialization logs:
```bash
docker logs ollama-init
```

### GPU Not Detected

Verify GPU access:
```bash
docker exec ollama-proxy nvidia-smi
```

If this fails, see [ollama-gpu-guide.md](ollama-gpu-guide.md) for setup instructions.

### API Returns 404

Ensure models are pulled:
```bash
docker exec ollama-proxy ollama list
```

If empty, manually pull:
```bash
docker exec -it ollama-proxy ollama pull llama3
```

### Connection Errors

Check if all services are healthy:
```bash
docker-compose ps
```

All should show `healthy` status.

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama locally (or via Docker)
# On separate terminal:
ollama serve

# Run FastAPI
python main.py
```

### Load Testing

```bash
# Install locust
pip install -r requirements-locust.txt

# Run load tests
python run_load_test.py

# Open http://localhost:8089
```

