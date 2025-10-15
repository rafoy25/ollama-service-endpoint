from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from pydantic import BaseModel
import requests
from typing import List, Optional
import httpx
import psycopg2
from concurrent.futures import ProcessPoolExecutor
import asyncio
import multiprocessing

db_params = {
    "host": "localhost",
    "port": 5432,
    "database": "brokentooth",
    "user": "postgres",
    "password": "web1234"
}

workers = multiprocessing.cpu_count()



conn = psycopg2.connect(**db_params)

app = FastAPI()


def is_prime(num: int) -> bool:
    if num <= 1:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def compute_primes_up_to(numbers: int) -> List[int]:
    primes = []
    for num in range(2, numbers + 1):
        if is_prime(num):
            primes.append(num)
    return primes

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/list_tables")
async def list_tables():
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            table_list = [table[0] for table in tables]
            return {"tables": table_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/api/cpu_intensive_task")
async def cpu_intensive_task(n: int, background_tasks: BackgroundTasks):
    try:
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            result = await loop.run_in_executor(pool, compute_primes_up_to, n)
            return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test:app", host="0.0.0.0", port=5000, reload=True)