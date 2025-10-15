from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import requests
import httpx
import time
from typing import Dict, Optional
import logging
import jwt
from datetime import datetime, timedelta

url = "http://localhost:11434"
app = FastAPI(title="LLM API", version="1.0.0")
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

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

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# JWT Helper Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role", "user")
        
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "username": username,
            "user_id": user_id,
            "role": role,
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Mock user database (use real database in production)
USERS_DB = {
    "admin": {"password": "admin123", "user_id": 1, "role": "admin"},
    "user1": {"password": "password123", "user_id": 2, "role": "user"},
    "demo": {"password": "demo123", "user_id": 3, "role": "user"}
}


# Authentication function
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user information"""
    return verify_jwt_token(credentials.credentials)

# Role-based access control
async def require_admin(user_info: dict = Depends(verify_token)):
    """Require admin role"""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info

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

@app.post("/api/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """Authenticate user and return JWT token"""
    username = login_request.username
    password = login_request.password
    
    # Verify user credentials
    if username not in USERS_DB or USERS_DB[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user = USERS_DB[username]
    
    # Create JWT token
    token_data = {
        "sub": username,
        "user_id": user["user_id"], 
        "role": user["role"]
    }
    
    access_token = create_access_token(data=token_data)
    
    logger.info(f"User {username} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600  # seconds
    }

@app.get("/api/list_models")
async def list_models(
    user_info: dict = Depends(verify_token),
    __: None = Depends(rate_limit)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/api/tags", timeout=10)
            response_data = response.json()
            
            if "error" in response_data:
                raise HTTPException(status_code=404, detail=response_data["error"])
            
            logger.info(f"Models listed by user {user_info.get('username')}")
            return response_data
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
@app.get("/api/running_models")
async def running_models(
    user_info: dict = Depends(require_admin),  # Only admins can see running models
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
    user_info: dict = Depends(verify_token),
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
    user_info: dict = Depends(verify_token),
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
