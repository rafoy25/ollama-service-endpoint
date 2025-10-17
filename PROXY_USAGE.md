# FastAPI Ollama Proxy Usage

## Overview
This FastAPI service now acts as a **transparent proxy** to Ollama. This means you can use `http://localhost:8000` (or your FastAPI host) as the base URL for any Ollama API endpoint, and it will automatically forward requests to the Ollama service.

## Use Case: RagFlow Integration
RagFlow asks users to provide a base URL for Ollama (typically `http://localhost:11434`). With this proxy, you can instead provide:

```
http://localhost:8000
```

RagFlow will then make requests like:
- `http://localhost:8000/api/embeddings`
- `http://localhost:8000/api/generate`
- `http://localhost:8000/api/chat`
- `http://localhost:8000/api/tags`

And all of these will be proxied to the actual Ollama service at `http://localhost:11434`.

## How It Works

1. **Catch-All Route**: The proxy uses a catch-all route (`/{path:path}`) that matches any URL path
2. **Request Forwarding**: It forwards the complete request including:
   - HTTP method (GET, POST, PUT, DELETE, etc.)
   - Headers (excluding host and content-length)
   - Request body
   - Query parameters
3. **Response Handling**: It properly handles both:
   - **Regular responses**: JSON data
   - **Streaming responses**: For endpoints like `/api/generate` with streaming enabled

## Example API Calls

### List Models
```bash
curl http://localhost:8000/api/tags
```

### Get Embeddings
```bash
curl -X POST http://localhost:8000/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mxbai-embed-large",
    "input": ["Hello world"]
  }'
```

### Generate Text (Streaming)
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "prompt": "Why is the sky blue?",
    "stream": true
  }'
```

### Check Ollama Version
```bash
curl http://localhost:8000/api/version
```

## Configuration

The Ollama service URL is configured via environment variable:

```bash
export OLLAMA_URL="http://localhost:11434"  # Default when running locally
export OLLAMA_URL="http://ollama:11434"     # Default when running in Docker
```

## Docker Usage

When running in Docker with docker-compose, the services are networked together:

1. **FastAPI** runs on port `8000` (exposed to host)
2. **Ollama** runs on port `11434` (internal to Docker network)

External applications (like RagFlow) connect to:
```
http://localhost:8000
```

And FastAPI proxies requests to:
```
http://ollama:11434
```

## Benefits

1. **Single Entry Point**: All Ollama requests go through FastAPI
2. **Middleware Support**: Benefit from CORS, authentication, rate limiting, etc.
3. **Monitoring**: Log and monitor all Ollama API usage
4. **Compatibility**: Works with any tool that expects standard Ollama API
5. **Flexibility**: Can add custom endpoints alongside the proxy

## Custom Endpoints

The proxy preserves your custom endpoints:
- `/api/health` - Health check
- `/api/list_models` - List available models
- `/api/running_models` - Show currently running models

These will use your custom implementations. All other paths are proxied to Ollama.
