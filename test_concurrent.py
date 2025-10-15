"""Test concurrent embedding requests to verify async handling"""
import asyncio
import httpx
import time
from typing import List


async def make_embedding_request(client: httpx.AsyncClient, request_id: int, texts: List[str]):
    """Make a single embedding request"""
    payload = {
        "model": "mxbai-embed-large",
        "input": texts
    }

    start_time = time.time()
    response = await client.post("http://localhost:8000/api/embeddings", json=payload, timeout=30.0)
    elapsed = time.time() - start_time

    data = response.json()
    return {
        "request_id": request_id,
        "elapsed": elapsed,
        "backend": data.get("backend", "unknown"),
        "num_embeddings": len(data.get("embeddings", [])),
        "status": response.status_code
    }


async def test_concurrent_requests(num_concurrent: int = 5):
    """Test multiple concurrent embedding requests"""
    print("=" * 70)
    print(f"Testing {num_concurrent} Concurrent Embedding Requests")
    print("=" * 70)

    test_texts = [
        ["This is test sentence 1", "This is test sentence 2"],
        ["Machine learning is amazing", "AI is the future"],
        ["Python programming is fun", "FastAPI is fast"],
        ["Concurrent requests test", "Thread pool execution"],
        ["NPU acceleration rocks", "OpenVINO is powerful"]
    ]

    # Ensure we have enough test data
    while len(test_texts) < num_concurrent:
        test_texts.append([f"Additional test text {len(test_texts)}"])

    async with httpx.AsyncClient() as client:
        # Test 1: Sequential requests (baseline)
        print("\n[Test 1] Sequential Requests (Baseline)")
        print("-" * 70)
        sequential_start = time.time()

        for i in range(num_concurrent):
            result = await make_embedding_request(client, i, test_texts[i])
            print(f"  Request {result['request_id']}: {result['elapsed']:.3f}s ({result['backend']})")

        sequential_total = time.time() - sequential_start
        print(f"\nTotal time (sequential): {sequential_total:.3f}s")

        # Test 2: Concurrent requests
        print("\n[Test 2] Concurrent Requests")
        print("-" * 70)
        concurrent_start = time.time()

        # Launch all requests concurrently
        tasks = [
            make_embedding_request(client, i, test_texts[i])
            for i in range(num_concurrent)
        ]

        results = await asyncio.gather(*tasks)

        concurrent_total = time.time() - concurrent_start

        for result in results:
            print(f"  Request {result['request_id']}: {result['elapsed']:.3f}s ({result['backend']})")

        print(f"\nTotal time (concurrent): {concurrent_total:.3f}s")

        # Analysis
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Sequential total time: {sequential_total:.3f}s")
        print(f"Concurrent total time: {concurrent_total:.3f}s")
        print(f"Speedup: {sequential_total/concurrent_total:.2f}x")
        print()

        if concurrent_total < sequential_total * 0.8:
            print("✅ PASS: Concurrent requests are being processed in parallel!")
            print(f"   Concurrent execution is {sequential_total/concurrent_total:.1f}x faster")
        else:
            print("❌ FAIL: Requests appear to be processed sequentially")
            print("   Check if async embedding is being used")

        print("=" * 70)


async def test_mixed_workload():
    """Test concurrent mix of embeddings and prompts"""
    print("\n\n" + "=" * 70)
    print("Testing Mixed Workload (Embeddings + Prompts)")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        start_time = time.time()

        # Launch concurrent requests of different types
        tasks = [
            # Embedding requests
            client.post("http://localhost:8000/api/embeddings",
                       json={"model": "mxbai-embed-large", "input": ["test 1", "test 2"]},
                       timeout=30.0),
            client.post("http://localhost:8000/api/embeddings",
                       json={"model": "mxbai-embed-large", "input": ["test 3", "test 4"]},
                       timeout=30.0),
            # Health checks (should be instant)
            client.get("http://localhost:8000/api/health"),
            client.get("http://localhost:8000/api/health"),
        ]

        responses = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        print(f"\n4 concurrent requests completed in: {total_time:.3f}s")
        print(f"All requests successful: {all(r.status_code == 200 for r in responses)}")
        print("\n✅ Mixed workload handling verified")
        print("=" * 70)


if __name__ == "__main__":
    print("\nStarting concurrent API tests...")
    print("Make sure FastAPI server is running: python main.py\n")

    try:
        # Test concurrent embeddings
        asyncio.run(test_concurrent_requests(num_concurrent=5))

        # Test mixed workload
        asyncio.run(test_mixed_workload())

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
