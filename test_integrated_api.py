"""Test the integrated FastAPI with NPU embeddings"""
import requests
import json
import time


def test_api():
    base_url = "http://localhost:8000"

    print("=" * 70)
    print("Testing FastAPI with NPU Embedding Integration")
    print("=" * 70)

    # Test 1: Health check
    print("\n[1] Testing health endpoint...")
    response = requests.get(f"{base_url}/api/health")
    print(f"    Status: {response.status_code}")
    print(f"    Response: {json.dumps(response.json(), indent=2)}")

    # Test 2: Embeddings with NPU
    print("\n[2] Testing embeddings endpoint (NPU)...")
    test_texts = [
        "This is a test sentence for embedding.",
        "Machine learning is fascinating.",
        "Python is a great programming language."
    ]

    payload = {
        "model": "mxbai-embed-large",
        "input": test_texts
    }

    start_time = time.time()
    response = requests.post(f"{base_url}/api/embeddings", json=payload)
    elapsed = time.time() - start_time

    print(f"    Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"    Backend: {data.get('backend', 'unknown')}")
        print(f"    Model: {data.get('model', 'unknown')}")
        print(f"    Number of embeddings: {len(data.get('embeddings', []))}")
        if data.get('embeddings'):
            print(f"    Embedding dimension: {len(data['embeddings'][0])}")
        print(f"    Time taken: {elapsed:.3f}s ({elapsed/len(test_texts):.3f}s per text)")
        print(f"    First embedding (10 dims): {data['embeddings'][0][:10]}")
    else:
        print(f"    Error: {response.text}")

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    print("\nMake sure FastAPI is running (python main.py)\n")
    time.sleep(1)

    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to FastAPI server.")
        print("Please start the server with: python main.py")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
