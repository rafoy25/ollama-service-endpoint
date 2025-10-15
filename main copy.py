from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import requests
import httpx
import time
from typing import Dict
import logging

url = "http://localhost:11434"
app = FastAPI(title="LLM API", version="1.0.0")
security = HTTPBearer()

# Rate limiting storage (use Redis in real production)
rate_limit_storage: Dict[str, list] = {}
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORSMiddleware_settings = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

app.add_middleware(CORSMiddleware, **CORSMiddleware_settings)

embedding_models = ["mxbai-embed-large", "nomic-embed-text", "all-minilm"]

class PromptsRequest(BaseModel):
    model: str = Field(default="llama3", max_length=50)
    prompt: str = Field(..., min_length=1, max_length=8000)  # Limit prompt size
    stream: bool = False

class EmbeddingsRequest(BaseModel):
    model: str = Field(default=embedding_models[0], max_length=50)
    input: list[str] = Field(..., max_items=100, description="Max 100 texts per request")


class ResponseModel(BaseModel):
    response: str


# Authentication function
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In production, verify JWT token or API key
    if credentials.credentials != "your-secret-api-key":
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return credentials.credentials

# Rate limiting function
async def rate_limit(request: Request):
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = []
    
    # Clean old requests
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check rate limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}

@app.get("/api/list_models")
async def list_models(
    _: str = Depends(verify_token),
    __: None = Depends(rate_limit)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/api/tags", timeout=10)
            response_data = response.json()
            
            if "error" in response_data:
                raise HTTPException(status_code=404, detail=response_data["error"])
            
            logger.info("Models listed successfully")
            return response_data
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
@app.get("/api/running_models")
async def running_models(
    _: str = Depends(verify_token),
    __: None = Depends(rate_limit)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/api/ps", timeout=10)
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch running models: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@app.post("/api/embeddings")
async def generate_embeddings(
    embeddings: EmbeddingsRequest,
    _: str = Depends(verify_token),
    __: None = Depends(rate_limit)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{url}/api/embed", json=embeddings.dict(), timeout=None)
            response_data = response.json()

            if "error" in response_data:
                raise HTTPException(status_code=404, detail=response_data["error"])
            return response.json()
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error connecting to the embeddings service")




@app.post("/api/prompts")
async def create_prompt(
    prompts: PromptsRequest,
    _: str = Depends(verify_token),
    __: None = Depends(rate_limit)
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{url}/api/generate", json=prompts.dict(), timeout=None)
            response_data = response.json()

            if "error" in response_data:
                raise HTTPException(status_code=404, detail=response_data["error"])
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
