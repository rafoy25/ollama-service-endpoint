# Docker Deployment Guide

Complete guide for deploying the Ollama FastAPI Proxy with Docker and GPU support.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Connecting External Services](#connecting-external-services)

---

## Prerequisites

### Required Software
- **Docker**: Version 20.10+ ([Install Guide](https://docs.docker.com/engine/install/))
- **Docker Compose**: V2+ with GPU support
- **NVIDIA GPU Drivers**: Latest version for your GPU
- **NVIDIA Container Toolkit**: For GPU passthrough ([Setup Guide](ollama-gpu-guide.md))

### System Requirements
- Ubuntu 20.04+ (or compatible Linux distribution)
- NVIDIA GPU with CUDA support
- At least 8GB RAM (16GB+ recommended for larger models)
- 20GB+ free disk space for models

### Verify Prerequisites

```bash
# 1. Check Docker
docker --version
docker compose version

# 2. Check NVIDIA drivers
nvidia-smi

# 3. Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

If any of these fail, see the [NVIDIA Container Toolkit Setup](ollama-gpu-guide.md).

---

## Quick Start

```bash
# 1. Clone or navigate to repository
cd /path/to/work

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 4. Pull a model in Ollama
docker exec -it ollama ollama pull llama3

# 5. Test the API
curl http://localhost:8000/api/health
curl http://localhost:8000/api/list_models
```

---

## Detailed Setup

### Step 1: Build and Start Services

```bash
# Build and start in detached mode
docker-compose up -d

# View startup logs
docker-compose logs -f
```

**Expected Output:**
```
✔ Network ollama-network  Created
✔ Volume ollama-data      Created
✔ Container ollama        Healthy
✔ Container fastapi-proxy Started
```

### Step 2: Verify GPU Access

```bash
# Check GPU is accessible from Ollama container
docker exec ollama nvidia-smi
```

You should see your GPU listed with driver information.

### Step 3: Pull Ollama Models

```bash
# Pull a chat model
docker exec -it ollama ollama pull llama3

# Pull an embedding model
docker exec -it ollama ollama pull mxbai-embed-large

# List all pulled models
docker exec -it ollama ollama list
```

### Step 4: Test FastAPI Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# List models
curl http://localhost:8000/api/list_models

# Test chat completion
curl -X POST http://localhost:8000/api/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "prompt": "Say hello!",
    "stream": false
  }'

# Test embeddings
curl -X POST http://localhost:8000/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mxbai-embed-large",
    "input": ["Hello world", "Test embedding"]
  }'
```

---

## Verification

### Check Service Status

```bash
# View all containers
docker-compose ps

# Expected output:
# NAME            STATUS                    PORTS
# fastapi-proxy   Up (healthy)             0.0.0.0:8000->8000/tcp
# ollama          Up (healthy)             0.0.0.0:11434->11434/tcp
```

### Check Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs fastapi
docker-compose logs ollama

# Follow logs in real-time
docker-compose logs -f fastapi
```

### Check Network Connectivity

```bash
# Test internal communication (FastAPI -> Ollama)
docker exec fastapi-proxy curl http://ollama:11434/api/tags

# Test from host
curl http://localhost:8000/api/health
curl http://localhost:11434/api/tags
```

---

## Troubleshooting

### Issue: GPU Not Detected

**Symptoms:**
```
Error: NVIDIA driver not found
```

**Solution:**
1. Verify NVIDIA drivers: `nvidia-smi`
2. Reinstall NVIDIA Container Toolkit: See [ollama-gpu-guide.md](ollama-gpu-guide.md)
3. Restart Docker: `sudo systemctl restart docker`
4. Restart services: `docker-compose restart`

### Issue: Ollama Health Check Failing

**Symptoms:**
```
Container ollama is unhealthy
```

**Solution:**
```bash
# Check Ollama logs
docker logs ollama

# Restart Ollama
docker-compose restart ollama

# Check if Ollama is responding
docker exec ollama curl http://localhost:11434/api/tags
```

### Issue: FastAPI Can't Connect to Ollama

**Symptoms:**
```
Connection error: Cannot connect to http://ollama:11434
```

**Solution:**
```bash
# Verify network
docker network inspect ollama-network

# Check if both containers are on the network
docker network inspect ollama-network | grep -A 10 Containers

# Restart FastAPI
docker-compose restart fastapi
```

### Issue: Port Already in Use

**Symptoms:**
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution:**
```bash
# Find process using the port
sudo lsof -i :8000
# or
sudo netstat -tulpn | grep 8000

# Kill the process or change port in docker-compose.yml
# Example: Change "8000:8000" to "8001:8000"
```

### Issue: Models Not Persisting

**Symptoms:**
Models disappear after `docker-compose down`

**Solution:**
```bash
# Check volume exists
docker volume ls | grep ollama-data

# Don't use -v flag when stopping
docker-compose down  # Good
docker-compose down -v  # Bad (deletes volumes)

# If volume was deleted, recreate and re-pull models
docker-compose up -d
docker exec -it ollama ollama pull llama3
```

---

## Connecting External Services

### For RAGFlow or Other Containers

#### Method 1: Join the Network (Recommended)

Add to your external service's `docker-compose.yml`:

```yaml
services:
  ragflow:
    image: your-ragflow-image:latest
    networks:
      - ollama-network
    environment:
      - LLM_API_URL=http://fastapi-proxy:8000

networks:
  ollama-network:
    external: true
```

Then start your service:
```bash
docker-compose up -d
```

#### Method 2: Access via Host Network

Configure your external service to access:
- **Linux**: `http://<host-ip>:8000`
- **Docker Desktop**: `http://host.docker.internal:8000`

### Testing External Connectivity

```bash
# From within external container
docker exec <your-container> curl http://fastapi-proxy:8000/api/health

# From host
curl http://localhost:8000/api/health
```

---

## Management Commands

### Starting and Stopping

```bash
# Start services
docker-compose up -d

# Stop services (keeps data)
docker-compose down

# Stop and remove volumes (deletes model data)
docker-compose down -v

# Restart specific service
docker-compose restart fastapi
docker-compose restart ollama
```

### Updating and Rebuilding

```bash
# After code changes
docker-compose up -d --build

# Force rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Viewing Resources

```bash
# View logs
docker-compose logs -f

# View resource usage
docker stats

# View volumes
docker volume ls

# Inspect volume
docker volume inspect ollama-data
```

### Accessing Container Shells

```bash
# FastAPI container
docker exec -it fastapi-proxy bash

# Ollama container
docker exec -it ollama bash

# Run commands in Ollama
docker exec -it ollama ollama list
docker exec -it ollama ollama run llama3
```

---

## Performance Tips

### GPU Memory Management

```bash
# Check GPU memory usage
docker exec ollama nvidia-smi

# If models are too large, use smaller variants
docker exec -it ollama ollama pull llama3:8b  # Instead of 70b
```

### Docker Resource Limits

Add to `docker-compose.yml` if needed:

```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
```

### Network Performance

For production, consider:
- Using host network mode for reduced latency
- Adjusting timeout values in `main.py`
- Enabling HTTP/2 in uvicorn

---

## Security Considerations

### Production Deployment

1. **Remove debug ports**: Comment out Ollama's `11434:11434` port mapping
2. **Restrict CORS**: Update `allow_origins` in `main.py` to specific domains
3. **Add authentication**: Implement API key authentication in FastAPI
4. **Use reverse proxy**: Put nginx/traefik in front of FastAPI
5. **Enable HTTPS**: Use TLS certificates for production

### Network Isolation

```yaml
# More restrictive network settings
networks:
  ollama-network:
    driver: bridge
    internal: true  # No external access
```

---

## Backup and Recovery

### Backup Ollama Models

```bash
# Create backup
docker run --rm -v ollama-data:/data -v $(pwd):/backup ubuntu \
  tar czf /backup/ollama-backup.tar.gz /data

# Restore backup
docker run --rm -v ollama-data:/data -v $(pwd):/backup ubuntu \
  tar xzf /backup/ollama-backup.tar.gz -C /
```

---

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose GPU Support](https://docs.docker.com/compose/gpu-support/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

---

## Support

For issues specific to this setup:
1. Check logs: `docker-compose logs`
2. Verify GPU: `docker exec ollama nvidia-smi`
3. Test connectivity: `curl http://localhost:8000/api/health`
4. Review [CLAUDE.md](CLAUDE.md) for architecture details
