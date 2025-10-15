"""Test NPU embedding service with static shapes"""
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from npu_embedding_service_static import NPUEmbeddingServiceStatic
import time


def test_embedding_service():
    print("=" * 60)
    print("Testing NPU Embedding Service (STATIC SHAPES)")
    print("=" * 60)

    # Initialize service
    service = NPUEmbeddingServiceStatic()

    # Get device info
    info = service.get_device_info()
    print(f"\nDevice: {info['device']}")
    print(f"Device Name: {info['device_name']}")
    print(f"Available Devices: {', '.join(info['available_devices'])}")
    print()

    # Load model (NPU-compatible with static shapes)
    model_path = "./models/mxbai-embed-large-ov-npu/model.xml"
    print(f"Loading model from: {model_path}")
    service.load_model(model_path)

    # Show static configuration
    info = service.get_device_info()
    print(f"\nStatic Shape Configuration:")
    print(f"  Batch size: {info['batch_size']}")
    print(f"  Max sequence length: {info['max_seq_length']}")
    print()

    # Test embeddings
    test_texts = [
        "This is a test sentence for embedding generation.",
        "Machine learning is a subset of artificial intelligence.",
        "Python is a great programming language for data science."
    ]

    print(f"Generating embeddings for {len(test_texts)} texts...")
    start_time = time.time()

    embeddings = service.embed(test_texts)

    elapsed = time.time() - start_time

    print(f"\nResults:")
    print(f"  - Number of embeddings: {len(embeddings)}")
    print(f"  - Embedding dimension: {len(embeddings[0])}")
    print(f"  - Time taken: {elapsed:.3f}s ({elapsed/len(test_texts):.3f}s per text)")
    print(f"  - Device used: {info['device']}")

    # Show sample embedding
    print(f"\nSample embedding (first 10 dims):")
    print(f"  {embeddings[0][:10]}")

    print("\n" + "=" * 60)
    print("[SUCCESS] NPU embedding service is working with static shapes!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_embedding_service()
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
