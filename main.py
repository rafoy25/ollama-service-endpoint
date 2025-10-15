from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import httpx
import os

# Ollama URL - configurable via environment variable for Docker deployment
# Default: http://ollama:11434 (Docker service name)
# Override: Set OLLAMA_URL environment variable
url = os.getenv("OLLAMA_URL", "http://localhost:11434")

app = FastAPI(title="Ollama Proxy API", version="1.0.0")

CORSMiddleware_settings = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

app.add_middleware(CORSMiddleware, **CORSMiddleware_settings)

embedding_models = ["mxbai-embed-large"]

class PromptsRequest(BaseModel):
    model : str = "gemma3:4b"
    prompt : str
    stream : bool = True

class EmbeddingsRequest(BaseModel):
    model: str = embedding_models[0]
    input: list[str]


class ResponseModel(BaseModel):
    response: str


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


@app.post("/api/embeddings")
async def generate_embeddings(embeddings: EmbeddingsRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{url}/api/embed", json=embeddings.dict(), timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            if "error" in response_data:
                raise HTTPException(status_code=400, detail=response_data["error"])
            
            return response_data
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error from embeddings service")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")




@app.post("/api/prompts")
async def create_prompt(prompts: PromptsRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{url}/api/generate", json=prompts.dict(), timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            if "error" in response_data:
                raise HTTPException(status_code=400, detail=response_data["error"])
            
            return response_data
        
    except httpx.HTTPStatusError as e:
        print(e)
        raise HTTPException(status_code=e.response.status_code, detail="Error from generation service")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
