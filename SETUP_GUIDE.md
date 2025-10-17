# Ollama API Setup Guide

Professional setup guide for configuring your local Ollama LLM service with RagFlow or other applications.

## Quick Start

### 1. Start the Services

```bash
docker-compose up -d
```

This will start:
- **Ollama**: Local LLM engine with GPU support
- **Ollama API Proxy**: FastAPI service for easy access
- **Model Initialization**: Automatically downloads required models

### 2. Configure Your Application

Use one of these base URLs in RagFlow or your application:

| URL Option | Use Case | Setup Required |
|------------|----------|----------------|
| `http://localhost:8000` | Quick start, testing | None |
| `http://ollama-api.local:8000` | Professional, clear naming | Hosts file edit |
| `http://host.docker.internal:8000` | From other Docker containers | None (Docker Desktop) |

## Base URL Configuration Options

### Option 1: Default (localhost) ⚡

**Base URL:** `http://localhost:8000`

**Pros:**
- Works immediately, no setup
- Universal compatibility

**Cons:**
- Not descriptive
- Doesn't convey "local LLM"

**Use this for:** Quick testing, development

---

### Option 2: Custom Local Domain (Recommended) ⭐

**Base URL:** `http://ollama-api.local:8000`

**Pros:**
- Professional and descriptive
- Clearly indicates local service
- No port conflicts with other services

**Setup:**

#### Windows
1. Open Notepad as Administrator
2. Open file: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line:
   ```
   127.0.0.1    ollama-api.local
   ```
4. Save and close

#### Linux/Mac
1. Open terminal
2. Edit hosts file:
   ```bash
   sudo nano /etc/hosts
   ```
3. Add this line:
   ```
   127.0.0.1    ollama-api.local
   ```
4. Save (Ctrl+X, Y, Enter)

#### Verify
```bash
ping ollama-api.local
# Should respond from 127.0.0.1
```

**Use this for:** Production use, sharing with team, professional deployments

---

### Option 3: Docker Internal Access 🐳

**Base URL:** `http://host.docker.internal:8000`

**When to use:** If RagFlow is running in Docker and needs to access the Ollama service

**Setup:**
- Docker Desktop: Works automatically
- Linux: Add to docker run command:
  ```bash
  --add-host host.docker.internal:host-gateway
  ```

**Use this for:** Containerized applications

---

## RagFlow Configuration Examples

### Configuration Screen

When RagFlow asks for "Ollama Base URL", use:

```
http://ollama-api.local:8000
```

Or if you prefer localhost:

```
http://localhost:8000
```

### What RagFlow Will Access

RagFlow will automatically append API paths:
- Embeddings: `http://ollama-api.local:8000/api/embed`
- Generation: `http://ollama-api.local:8000/api/generate`
- Models: `http://ollama-api.local:8000/api/tags`

Everything is proxied transparently to Ollama!

---

## Advanced: Custom Port or Domain

### Change Port

Edit `docker-compose.yml`:

```yaml
fastapi:
  ports:
    - "8080:8000"  # Change 8080 to your preferred port
```

Then use: `http://ollama-api.local:8080`

### Use Standard HTTP Port (80)

```yaml
fastapi:
  ports:
    - "80:8000"
```

Then use: `http://ollama-api.local` (no port needed!)

**Note:** Port 80 requires administrator/sudo privileges.

---

## Multiple Custom Domains

Add multiple domains for different use cases:

**hosts file:**
```
127.0.0.1    ollama-api.local
127.0.0.1    local-llm.api
127.0.0.1    ai.local
127.0.0.1    rag.local
```

Then you can use any of these:
- `http://ollama-api.local:8000` (descriptive)
- `http://local-llm.api:8000` (emphasizes local LLM)
- `http://ai.local:8000` (short and simple)
- `http://rag.local:8000` (RAG-specific)

---

## Environment Variables

Customize your deployment with these environment variables:

Create a `.env` file:

```bash
# Models to download on startup (space-separated)
OLLAMA_MODELS=gemma3:4b mxbai-embed-large llama3:8b

# Internal Ollama URL (for proxy -> ollama communication)
OLLAMA_URL=http://ollama:11434

# Change exposed ports
FASTAPI_PORT=8000
OLLAMA_PORT=11434
```

Update `docker-compose.yml` to use them:

```yaml
fastapi:
  ports:
    - "${FASTAPI_PORT:-8000}:8000"
  environment:
    - OLLAMA_URL=${OLLAMA_URL:-http://ollama:11434}
```

---

## Testing Your Setup

### 1. Check Health

```bash
curl http://ollama-api.local:8000/api/health
# Should return: {"status":"ok"}
```

### 2. List Models

```bash
curl http://ollama-api.local:8000/api/tags
```

### 3. Test Embeddings

```bash
curl -X POST http://ollama-api.local:8000/api/embed \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mxbai-embed-large",
    "input": "Test embedding"
  }'
```

### 4. Test Generation

```bash
curl -X POST http://ollama-api.local:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:4b",
    "prompt": "What is AI?",
    "stream": false
  }'
```

---

## Troubleshooting

### "Cannot connect to ollama-api.local"

**Solution 1:** Check hosts file was edited correctly
```bash
# Windows
type C:\Windows\System32\drivers\etc\hosts | findstr ollama

# Linux/Mac
cat /etc/hosts | grep ollama
```

**Solution 2:** Flush DNS cache
```bash
# Windows
ipconfig /flushdns

# Linux
sudo systemctl restart systemd-resolved

# Mac
sudo dscacheutil -flushcache
```

### "Connection refused on port 8000"

Check if services are running:
```bash
docker-compose ps
```

Should show:
- `ollama-api` - running
- `ollama-proxy` - running

### "Port 8000 already in use"

Change the port in `docker-compose.yml`:
```yaml
fastapi:
  ports:
    - "8080:8000"  # Use 8080 instead
```

Then use: `http://ollama-api.local:8080`

---

## Best Practices for Production

### 1. Use Custom Domain
✅ `http://ollama-api.local:8000`
❌ `http://localhost:8000`

### 2. Document for Your Team

Create a team document with:
- The exact base URL to use
- Hosts file setup instructions
- Available models
- Example API calls

### 3. Monitor Health

Set up monitoring:
```bash
# Add to cron or Task Scheduler
*/5 * * * * curl -f http://ollama-api.local:8000/api/health || alert
```

### 4. Version Control

Commit these files to git:
- `docker-compose.yml`
- `Dockerfile`
- `.env.example` (template)
- `SETUP_GUIDE.md` (this file)

Don't commit:
- `.env` (actual credentials/config)

---

## Summary: Recommended Base URL

**For your users in RagFlow, instruct them to use:**

```
http://ollama-api.local:8000
```

**Benefits:**
- ✅ Professional and descriptive
- ✅ Clearly indicates "local Ollama API"
- ✅ Easy to remember
- ✅ No confusion with other services
- ✅ Works on all platforms (with simple hosts file edit)

**Setup time:** 30 seconds (one-time hosts file edit)

This provides the best balance of professionalism, clarity, and ease of use!
