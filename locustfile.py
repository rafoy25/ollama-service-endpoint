"""
Locust load testing file for Ollama FastAPI Proxy
Tests concurrent requests to verify connection pooling and performance.

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 in your browser to configure and start the test.
"""

from locust import HttpUser, task, between, events
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaProxyUser(HttpUser):
    """
    Simulates a user making requests to the Ollama proxy.
    Focuses on embeddings and generation - the most used endpoints in RAG systems.
    """

    # Wait between 1-3 seconds between requests (simulates real user behavior)
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts."""
        logger.info(f"User {self.environment.runner.user_count} started")

    @task(5)  # Weight 5: Embeddings are the most common in RAG
    def test_single_embedding_1(self):
        """
        Test single embedding - typical RAG workflow.
        Ollama's /api/embed only supports one text at a time.
        """
        payload = {
            "model": "mxbai-embed-large",
            "input": "This is a test document for embedding generation."
        }

        with self.client.post(
            "/api/embed",
            json=payload,
            catch_response=True,
            name="/api/embed (single text)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "embeddings" in data or "embedding" in data:
                        response.success()
                        logger.debug(f"Embedding successful")
                    else:
                        response.failure("Invalid embeddings response structure")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def test_single_embedding_2(self):
        """Test single text embedding - query embedding scenario."""
        payload = {
            "model": "mxbai-embed-large",
            "input": "What is the meaning of artificial intelligence?"
        }

        with self.client.post(
            "/api/embed",
            json=payload,
            catch_response=True,
            name="/api/embed (query)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "embeddings" in data or "embedding" in data:
                        response.success()
                    else:
                        response.failure("Invalid embeddings response")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def test_long_text_embedding(self):
        """
        Test embedding with longer text.
        This simulates processing a paragraph or section.
        """
        payload = {
            "model": "mxbai-embed-large",
            "input": (
                "This is a longer text chunk for concurrent processing test. "
                "It represents a realistic document section that needs embedding. "
                "In a real RAG system, documents are split into chunks of this size. "
                "Each chunk is then embedded separately and stored in a vector database. "
                "When users query the system, their question is embedded and compared to these stored embeddings."
            )
        }

        with self.client.post(
            "/api/embed",
            json=payload,
            catch_response=True,
            name="/api/embed (long text)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "embeddings" in data or "embedding" in data:
                        response.success()
                        logger.debug(f"Long text embedding successful")
                    else:
                        response.failure("Invalid embeddings response structure")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def test_list_models(self):
        """Test listing available models through the proxy."""
        with self.client.get(
            "/api/tags",
            catch_response=True,
            name="/api/tags (list models)"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "models" in data:
                        response.success()
                    else:
                        response.failure("Invalid models list response")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def test_version(self):
        """Test Ollama version endpoint through the proxy."""
        with self.client.get(
            "/api/version",
            catch_response=True,
            name="/api/version"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "version" in data:
                        response.success()
                    else:
                        response.failure("Invalid version response")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(4)  # Weight 4: Generation is heavily used in RAG for Q&A
    def test_generation_non_streaming(self):
        """
        Test text generation without streaming - typical RAG Q&A scenario.
        This is used when RagFlow generates answers based on retrieved context.
        """
        payload = {
            "model": "gemma3:4b",
            "prompt": "What is machine learning? Provide a brief explanation.",
            "stream": False
        }

        with self.client.post(
            "/api/generate",
            json=payload,
            catch_response=True,
            name="/api/generate (non-streaming)",
            timeout=60
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "response" in data:
                        response.success()
                        logger.debug(f"Generation successful: {len(data.get('response', ''))} chars")
                    else:
                        response.failure("Invalid generation response")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)  # Weight 3: Streaming generation for real-time responses
    def test_generation_streaming(self):
        """
        Test streaming text generation - real-time RAG responses.
        Used when RagFlow streams answers to users in real-time.
        """
        payload = {
            "model": "gemma3:4b",
            "prompt": "Explain the concept of neural networks in simple terms.",
            "stream": True
        }

        with self.client.post(
            "/api/generate",
            json=payload,
            catch_response=True,
            name="/api/generate (streaming)",
            timeout=60,
            stream=True
        ) as response:
            if response.status_code == 200:
                try:
                    # Consume streaming response
                    chunks_received = 0
                    for line in response.iter_lines():
                        if line:
                            chunks_received += 1
                            # Parse NDJSON
                            try:
                                json.loads(line)
                            except json.JSONDecodeError:
                                response.failure("Invalid JSON in stream")
                                return

                    if chunks_received > 0:
                        response.success()
                        logger.debug(f"Stream successful: {chunks_received} chunks")
                    else:
                        response.failure("No chunks received in stream")
                except Exception as e:
                    response.failure(f"Stream error: {str(e)}")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def test_generation_with_context(self):
        """
        Test generation with RAG context - most realistic RAG scenario.
        Simulates answering a question based on retrieved documents.
        """
        context = (
            "Context: Neural networks are computing systems inspired by biological neural networks. "
            "They consist of interconnected nodes (neurons) organized in layers. "
            "These networks learn patterns from data through a process called training."
        )

        payload = {
            "model": "gemma3:4b",
            "prompt": f"{context}\n\nQuestion: How do neural networks learn?\nAnswer:",
            "stream": False
        }

        with self.client.post(
            "/api/generate",
            json=payload,
            catch_response=True,
            name="/api/generate (with context)",
            timeout=60
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "response" in data:
                        response.success()
                    else:
                        response.failure("Invalid generation response")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def test_health(self):
        """Test custom health check endpoint."""
        with self.client.get(
            "/api/health",
            catch_response=True,
            name="/api/health"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok":
                        response.success()
                    else:
                        response.failure("Health check failed")
                except json.JSONDecodeError:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")


class HeavyLoadUser(HttpUser):
    """
    Simulates heavy load with minimal wait time between requests.
    Use this to stress test the proxy and connection pooling.
    Mix of embeddings and generation to test realistic concurrent load.
    """

    # Minimal wait time for stress testing
    wait_time = between(0.1, 0.5)

    @task(3)  # Focus more on embeddings as they're faster
    def stress_test_embeddings(self):
        """Rapid-fire embedding requests to test connection pooling."""
        payload = {
            "model": "mxbai-embed-large",
            "input": "Stress test embedding request for testing high concurrency and connection pool validation"
        }

        self.client.post(
            "/api/embed",
            json=payload,
            name="/api/embed (stress)"
        )

    @task(1)  # Less frequent generation to avoid overwhelming Ollama
    def stress_test_generation(self):
        """Rapid-fire generation requests with very short prompts."""
        payload = {
            "model": "gemma3:4b",
            "prompt": "Answer in 3 words: What is AI?",
            "stream": False,
            "options": {
                "num_predict": 10  # Limit response length for faster completion
            }
        }

        self.client.post(
            "/api/generate",
            json=payload,
            name="/api/generate (stress)",
            timeout=60  # Increased timeout for stress scenarios
        )


# Event handlers for logging test results
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    logger.info("=" * 60)
    logger.info("Starting Ollama Proxy Load Test")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    logger.info("=" * 60)
    logger.info("Load Test Complete")
    logger.info("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests for debugging."""
    if response_time > 5000:  # Log requests slower than 5 seconds
        logger.warning(
            f"Slow request detected: {request_type} {name} "
            f"took {response_time:.0f}ms"
        )
