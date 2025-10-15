"""
NPU-Accelerated Embedding Service using OpenVINO
Automatically selects best available device: NPU > GPU > CPU
Thread-safe for concurrent async requests
"""
import openvino as ov
from transformers import AutoTokenizer
from typing import List
import numpy as np
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NPUEmbeddingService:
    """Embedding service that uses Intel NPU/GPU/CPU via OpenVINO (thread-safe)"""

    def __init__(self, model_name: str = "mixedbread-ai/mxbai-embed-large-v1", max_workers: int = 4):
        self.model_name = model_name
        self.core = ov.Core()
        self.compiled_model = None
        self.tokenizer = None
        self.device = None
        self.model_loaded = False
        # Thread pool for async execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        # Lock for thread-safe tokenizer access
        self._lock = threading.Lock()

    def _select_device(self) -> str:
        """Select best available device: NPU > GPU > CPU"""
        devices = self.core.available_devices

        # Priority order
        if "NPU" in devices:
            logger.info("🚀 Using Intel NPU (AI Boost)")
            return "NPU"
        elif "GPU" in devices:
            logger.info("⚡ Using Intel iGPU")
            return "GPU"
        else:
            logger.info("💻 Using CPU")
            return "CPU"

    def load_model(self, model_path: str):
        """Load OpenVINO IR model"""
        try:
            self.device = self._select_device()

            # Load tokenizer
            logger.info(f"Loading tokenizer for {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Load and compile OpenVINO model
            logger.info(f"Loading OpenVINO model from {model_path}...")
            model = self.core.read_model(model_path)

            logger.info(f"Compiling model for {self.device}...")
            self.compiled_model = self.core.compile_model(model, self.device)

            self.model_loaded = True
            logger.info(f"✅ Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise

    def _embed_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding generation (internal use)"""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Tokenize with thread lock (tokenizer is not thread-safe)
            with self._lock:
                encoded = self.tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="np"
                )

            # Get model inputs - the traced model expects ordered inputs
            input_info = self.compiled_model.inputs
            logger.debug(f"Model expects {len(input_info)} inputs")

            # Create inputs in the order model expects
            if len(input_info) == 2:
                # Model expects: (input_ids, attention_mask)
                inputs = [encoded["input_ids"], encoded["attention_mask"]]
            else:
                # Fallback: try dictionary
                inputs = {
                    "input_ids": encoded["input_ids"],
                    "attention_mask": encoded["attention_mask"]
                }

            # OpenVINO inference (thread-safe)
            result = self.compiled_model(inputs)

            # Get embeddings from output
            # The output is the last hidden state from BERT
            output_keys = list(result.keys())
            embeddings = result[output_keys[0]]

            # Mean pooling
            attention_mask = encoded["attention_mask"]
            mask_expanded = np.expand_dims(attention_mask, axis=-1)
            sum_embeddings = np.sum(embeddings * mask_expanded, axis=1)
            sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
            embeddings_mean = sum_embeddings / sum_mask

            # Normalize
            embeddings_normalized = embeddings_mean / np.linalg.norm(embeddings_mean, axis=1, keepdims=True)

            return embeddings_normalized.tolist()

        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            raise

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings (synchronous, for backwards compatibility)"""
        return self._embed_sync(texts)

    async def embed_async(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings asynchronously (non-blocking for concurrent requests)"""
        loop = asyncio.get_event_loop()
        # Run blocking embedding in thread pool to avoid blocking event loop
        return await loop.run_in_executor(self.executor, self._embed_sync, texts)

    def get_device_info(self) -> dict:
        """Get information about the device being used"""
        if not self.device:
            self.device = self._select_device()

        device_name = self.core.get_property(self.device, "FULL_DEVICE_NAME")

        return {
            "device": self.device,
            "device_name": device_name,
            "model_loaded": self.model_loaded,
            "available_devices": self.core.available_devices
        }


# Singleton instance
_embedding_service = None

def get_embedding_service() -> NPUEmbeddingService:
    """Get or create singleton embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = NPUEmbeddingService()
    return _embedding_service
