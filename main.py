from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
import requests
import httpx
import os
import json
from contextlib import asynccontextmanager

# Ollama URL - configurable via environment variable for Docker deployment
# Default: http://ollama:11434 (Docker service name)
# Override: Set OLLAMA_URL environment variable
url = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Global HTTP client for connection pooling and better concurrency
http_client = None

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Creates a persistent httpx.AsyncClient for connection pooling.
    """
    global http_client
    # Startup: Create a persistent HTTP client with connection pooling
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(300.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        follow_redirects=True
    )
    yield
    # Shutdown: Close the HTTP client
    await http_client.aclose()

app = FastAPI(title="Ollama Proxy API", version="1.0.0", lifespan=lifespan)

CORSMiddleware_settings = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

app.add_middleware(CORSMiddleware, **CORSMiddleware_settings)



@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/list_models")
async def list_models():
    try:
        response = requests.get(f"{url}/api/tags")
        response.raise_for_status()
        
        response_data = response.json()
        if "error" in response_data:
            raise HTTPException(status_code=404, detail=response_data["error"])
        
        return response_data
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail="HTTP error from model service")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}") 
    
@app.get("/api/running_models")
async def running_models():
    try:
        response = requests.get(f"{url}/api/ps")
        response.raise_for_status()
        
        response_data = response.json()
        if "error" in response_data:
            raise HTTPException(status_code=404, detail=response_data["error"])
        
        return response_data
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail="HTTP error from model service")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


# REMOVED: Custom /api/embeddings endpoint
# Let the catch-all proxy handle all Ollama API requests transparently
# This ensures compatibility with RagFlow and other Ollama clients




# REMOVED: Custom /api/prompts endpoint
# Let the catch-all proxy handle all Ollama API requests transparently
# This ensures compatibility with RagFlow and other Ollama clients


# Catch-all proxy for any Ollama API endpoint
# This allows RagFlow to use http://localhost:8000 as the base URL
# and it will proxy all requests to the Ollama service
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_to_ollama(request: Request, path: str):
    """
    Proxy all requests to Ollama service.
    This enables RagFlow to use FastAPI as a transparent proxy to Ollama.
    """
    # Skip if it's one of our custom endpoints (already handled above)
    if path.startswith("api/health") or path.startswith("api/list_models") or path.startswith("api/running_models"):
        # These are handled by specific endpoints above
        pass

    # Build the target URL
    target_url = f"{url}/{path}"

    # Get query parameters
    query_params = str(request.url.query)
    if query_params:
        target_url = f"{target_url}?{query_params}"

    try:
        # Get request body if present
        body = await request.body()

        # Forward the request to Ollama using the shared HTTP client
        response = await http_client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers={
                key: value for key, value in request.headers.items()
                if key.lower() not in ["host", "content-length"]
            },
        )

        # Check if response is streaming (common for Ollama generate endpoints)
        content_type = response.headers.get("content-type", "")
        if "stream" in content_type or "text/event-stream" in content_type or response.headers.get("transfer-encoding") == "chunked":
            # Return streaming response
            async def generate():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                generate(),
                status_code=response.status_code,
                headers={
                    key: value for key, value in response.headers.items()
                    if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]
                },
                media_type=content_type or "application/json"
            )
        else:
            # Return regular response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers={
                    key: value for key, value in response.headers.items()
                    if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]
                },
                media_type=content_type or "application/json"
            )

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Proxy request failed: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error from Ollama service")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
