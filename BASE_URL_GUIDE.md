# Professional Base URL Setup for RagFlow

## The Problem ❌

**Generic URL:**
```
http://localhost:8000
```

**Issues:**
- Doesn't convey professionalism
- No indication it's a local LLM service
- Could be any service on port 8000
- Confusing for end users

## The Solution ✅

**Professional URL:**
```
http://ollama-api.local:8000
```

**Benefits:**
- ✅ Descriptive and professional
- ✅ Clearly indicates "Ollama API"
- ✅ Shows it's a local service
- ✅ Easy to remember
- ✅ Avoids confusion

---

## Quick Setup (30 seconds)

### Windows

1. **Open Notepad as Administrator**
   - Right-click Notepad → "Run as administrator"

2. **Open hosts file**
   - File → Open → `C:\Windows\System32\drivers\etc\hosts`

3. **Add this line at the end:**
   ```
   127.0.0.1    ollama-api.local
   ```

4. **Save and close**

### Linux / Mac

1. **Edit hosts file:**
   ```bash
   sudo nano /etc/hosts
   ```

2. **Add this line at the end:**
   ```
   127.0.0.1    ollama-api.local
   ```

3. **Save (Ctrl+X, Y, Enter)**

### Verify

```bash
ping ollama-api.local
# Should respond from 127.0.0.1
```

---

## Usage in RagFlow

### Before (Generic)
```
Ollama Base URL: http://localhost:8000
```

### After (Professional)
```
Ollama Base URL: http://ollama-api.local:8000
```

RagFlow will automatically use:
- `http://ollama-api.local:8000/api/embed` (embeddings)
- `http://ollama-api.local:8000/api/generate` (generation)
- `http://ollama-api.local:8000/api/tags` (list models)

---

## Alternative Options

### Option 1: Short and Simple
```
127.0.0.1    ai.local
```
Base URL: `http://ai.local:8000`

### Option 2: RAG-Focused
```
127.0.0.1    rag-api.local
```
Base URL: `http://rag-api.local:8000`

### Option 3: LLM-Focused
```
127.0.0.1    local-llm.api
```
Base URL: `http://local-llm.api:8000`

### Option 4: Multiple Aliases
```
127.0.0.1    ollama-api.local ai.local rag.local
```
Then use any of these:
- `http://ollama-api.local:8000`
- `http://ai.local:8000`
- `http://rag.local:8000`

---

## Docker Compose Changes

The `docker-compose.yml` has been updated with a descriptive container name:

```yaml
fastapi:
  container_name: ollama-api        # Descriptive name
  hostname: ollama-api              # Internal hostname
  ports:
    - "8000:8000"
```

This ensures the service is clearly identified everywhere.

---

## Troubleshooting

### "Can't resolve ollama-api.local"

**Check hosts file:**
```bash
# Windows
type C:\Windows\System32\drivers\etc\hosts | findstr ollama

# Linux/Mac
cat /etc/hosts | grep ollama
```

Should show: `127.0.0.1    ollama-api.local`

**Flush DNS cache:**
```bash
# Windows
ipconfig /flushdns

# Linux
sudo systemctl restart systemd-resolved

# Mac
sudo dscacheutil -flushcache
```

### "Still using localhost"

Browser may have cached the old URL. Use Ctrl+Shift+R to hard refresh.

---

## User Instructions Template

Copy this for your users:

```
📝 Ollama API Setup Instructions

1. Edit your hosts file:
   - Windows: C:\Windows\System32\drivers\etc\hosts (as Administrator)
   - Mac/Linux: /etc/hosts (with sudo)

2. Add this line:
   127.0.0.1    ollama-api.local

3. Save the file

4. In RagFlow, use this base URL:
   http://ollama-api.local:8000

That's it! You're now using a professional local LLM API.
```

---

## Why This Matters

### For Users
- Professional appearance
- Clear understanding of what the service is
- Easy to communicate ("use ollama-api.local")
- Memorable and descriptive

### For Support
- Fewer "what port?" questions
- Clear documentation
- Easy troubleshooting
- Professional image

### For Development
- Clear service identification
- No confusion with other local services
- Consistent across team
- Production-ready naming

---

## Summary

**Recommendation:** Use `http://ollama-api.local:8000`

This provides the best balance of:
- Professionalism ✅
- Clarity ✅
- Ease of use ✅
- User understanding ✅

Setup time: **30 seconds** (one-time hosts file edit)
