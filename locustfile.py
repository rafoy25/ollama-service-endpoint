from locust import HttpUser, task, between
import random
import json

class FastAPIUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    host = "http://localhost:8000"
    
    def on_start(self):
        """Called when a user starts"""
        # Test health check on start
        self.client.get("/api/health")
    
    @task(3)
    def test_health_check(self):
        """Test the health endpoint (lightweight)"""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def test_list_models(self):
        """Test listing available models"""
        with self.client.get("/api/list_models", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List models failed: {response.status_code}")
    
    @task(1)
    def test_running_models(self):
        """Test getting running models"""
        with self.client.get("/api/running_models", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Running models failed: {response.status_code}")
    
    @task(5)
    def test_chat_prompts(self):
        """Test chat/prompt generation (main feature)"""
        prompts = [
            "Hello, how are you?",
            "What is the capital of France?",
            "Explain quantum computing in simple terms.",
            "Write a short poem about coding.",
            "What's 2+2?",
            "Tell me a joke.",
            "Explain the concept of recursion.",
            "What is machine learning?",
        ]
        
        payload = {
            "model": "llama3",
            "prompt": random.choice(prompts),
            "stream": False
        }
        
        with self.client.post("/api/prompts", 
                            json=payload,
                            catch_response=True,
                            timeout=60) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "error" in data:
                        response.failure(f"API returned error: {data['error']}")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Prompt failed: {response.status_code}")
    
    @task(2)
    def test_embeddings(self):
        """Test embedding generation"""
        texts = [
            ["This is a test document for embedding."],
            ["Machine learning is a subset of artificial intelligence."],
            ["Python is a great programming language."],
            ["FastAPI makes building APIs easy."],
            ["Embeddings convert text to numerical vectors."],
        ]
        
        payload = {
            "model": "mxbai-embed-large",
            "input": random.choice(texts)
        }
        
        with self.client.post("/api/embeddings",
                            json=payload,
                            catch_response=True,
                            timeout=30) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "error" in data:
                        response.failure(f"Embedding API returned error: {data['error']}")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Embedding failed: {response.status_code}")

class HeavyUser(HttpUser):
    """Simulates users doing intensive operations"""
    wait_time = between(2, 5)
    host = "http://localhost:8000"
    weight = 1  # Lower weight = fewer of these users
    
    @task(1)
    def test_concurrent_embeddings_and_chat(self):
        """Test simultaneous embedding and chat to verify concurrency"""
        import threading
        import time
        
        # Start an embedding request
        embedding_payload = {
            "model": "mxbai-embed-large", 
            "input": ["This is a longer text for embedding that might take more time to process."]
        }
        
        # Start a chat request
        chat_payload = {
            "model": "llama3",
            "prompt": "Explain the theory of relativity in detail.",
            "stream": False
        }
        
        # Track results
        results = {"embedding": None, "chat": None}
        start_time = time.time()
        
        def embedding_request():
            with self.client.post("/api/embeddings", 
                                json=embedding_payload,
                                catch_response=True,
                                timeout=45) as response:
                results["embedding"] = response.status_code
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Concurrent embedding failed: {response.status_code}")
        
        def chat_request():
            with self.client.post("/api/prompts",
                                json=chat_payload,
                                catch_response=True,
                                timeout=45) as response:
                results["chat"] = response.status_code
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Concurrent chat failed: {response.status_code}")
        
        # Start both requests simultaneously
        embedding_thread = threading.Thread(target=embedding_request)
        chat_thread = threading.Thread(target=chat_request)
        
        embedding_thread.start()
        chat_thread.start()
        
        # Wait for both to complete
        embedding_thread.join()
        chat_thread.join()
        
        elapsed = time.time() - start_time
        print(f"Concurrent test completed in {elapsed:.2f}s - Embedding: {results['embedding']}, Chat: {results['chat']}")

# Custom user classes for different load patterns
class ChatOnlyUser(HttpUser):
    """Users who only chat"""
    wait_time = between(1, 2)
    host = "http://localhost:8000"
    weight = 3  # More of these users
    
    @task
    def chat_only(self):
        payload = {
            "model": "llama3",
            "prompt": "Quick question: what's the weather like?",
            "stream": False
        }
        
        self.client.post("/api/prompts", json=payload, timeout=30)

class EmbeddingOnlyUser(HttpUser):
    """Users who only generate embeddings"""
    wait_time = between(3, 6)
    host = "http://localhost:8000"
    weight = 1  # Fewer of these users
    
    @task
    def embedding_only(self):
        payload = {
            "model": "mxbai-embed-large",
            "input": ["Document for embedding processing."]
        }
        
        self.client.post("/api/embeddings", json=payload, timeout=20)