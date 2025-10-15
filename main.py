from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import httpx
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

url = "http://localhost:11434"
app = FastAPI()

CORSMiddleware_settings = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

app.add_middleware(CORSMiddleware, **CORSMiddleware_settings)

embedding_models = ["mxbai-embed-large", "nomic-embed-text", "all-minilm"]

# NPU Embedding Service Configuration
USE_NPU_EMBEDDINGS = os.getenv("USE_NPU_EMBEDDINGS", "true").lower() == "true"
NPU_MODEL_PATH = os.getenv("NPU_MODEL_PATH", "./models/mxbai-embed-large-ov/model.xml")
_npu_service = None

class PromptsRequest(BaseModel):
    model : str = "llama3"
    prompt : str
    stream : bool = False

class EmbeddingsRequest(BaseModel):
    model: str = embedding_models[0]
    input: list[str]


class ResponseModel(BaseModel):
    response: str


def get_npu_service():
    """Get or initialize NPU embedding service"""
    global _npu_service
    if _npu_service is None and USE_NPU_EMBEDDINGS:
        try:
            from npu_embedding_service import NPUEmbeddingService
            # Increase max_workers to handle more concurrent requests
            _npu_service = NPUEmbeddingService(max_workers=8)
            _npu_service.load_model(NPU_MODEL_PATH)
            logger.info(f"NPU embedding service initialized on {_npu_service.device} with 8 workers")
        except Exception as e:
            logger.warning(f"Failed to initialize NPU service: {e}. Falling back to Ollama.")
            _npu_service = False  # Mark as failed, don't retry
    return _npu_service if _npu_service is not False else None


@app.on_event("startup")
async def startup_event():
    """Initialize NPU service on startup"""
    if USE_NPU_EMBEDDINGS:
        get_npu_service()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    npu_status = "disabled"
    if USE_NPU_EMBEDDINGS:
        service = get_npu_service()
        if service:
            info = service.get_device_info()
            npu_status = f"enabled ({info['device']})"
        else:
            npu_status = "failed (using Ollama)"

    return {
        "status": "ok",
        "npu_embeddings": npu_status
    }

@app.get("/api/list_models")
async def list_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")

        response_data = response.json()
        if "error" in response_data:
            raise HTTPException(statuse_code=404, detail=response_data["error"])
        else:
            pass

        return response.json()
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail="HTTP error from model service")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}") 
    
@app.get("/api/running_models")
async def running_models():
    try:
        response = requests.get(f"{url}/api/ps")
        return response.json()
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail="HTTP error from model service")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


@app.post("/api/embeddings")
async def generate_embeddings(embeddings: EmbeddingsRequest):
    """Generate embeddings using NPU (if available) or Ollama (fallback)"""

    # Try NPU first if enabled
    npu_service = get_npu_service()
    if npu_service and embeddings.model == "mxbai-embed-large":
        try:
            logger.info(f"Using NPU for embeddings ({len(embeddings.input)} texts)")
            # Use async version to avoid blocking event loop (supports concurrency)
            embedding_vectors = await npu_service.embed_async(embeddings.input)

            # Format response to match Ollama's format
            return {
                "model": embeddings.model,
                "embeddings": embedding_vectors,
                "backend": "npu"
            }

        except Exception as e:
            logger.warning(f"NPU embedding failed: {e}. Falling back to Ollama.")
            import traceback
            logger.debug(traceback.format_exc())
            # Fall through to Ollama

    # Fallback to Ollama
    try:
        logger.info(f"Using Ollama for embeddings ({len(embeddings.input)} texts)")
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{url}/api/embed", json=embeddings.dict(), timeout=None)
            response_data = response.json()

            if "error" in response_data:
                raise HTTPException(status_code=404, detail=response_data["error"])

            # Add backend info
            result = response.json()
            result["backend"] = "ollama"
            return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error from embeddings service")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")




@app.post("/api/prompts")
async def create_prompt(prompts: PromptsRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{url}/api/generate", json=prompts.dict(), timeout=None)
            response_data = response.json()

            if "error" in response_data:
                raise HTTPException(status_code=404, detail=response_data["error"])
            return response.json()
        
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Error from generation service")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
