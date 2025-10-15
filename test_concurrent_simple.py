"""Simple concurrent test without unicode issues"""
import asyncio
import httpx
import time


async def make_request(client, request_id):
    """Make single embedding request"""
    payload = {
        "model": "mxbai-embed-large",
        "input": [f"Test text {request_id}", "Another test"]
    }

    start = time.time()
    response = await client.post("http://localhost:8000/api/embeddings", json=payload, timeout=30.0)
    elapsed = time.time() - start

    data = response.json()
    return {
        "id": request_id,
        "time": elapsed,
        "backend": data.get("backend"),
        "success": response.status_code == 200
    }


async def test_concurrent():
    """Test concurrent requests"""
    print("=" * 70)
    print("Concurrent Embedding Test")
    print("=" * 70)

    num_requests = 5

    async with httpx.AsyncClient() as client:
        # Sequential
        print("\n[1] Sequential Requests")
        seq_start = time.time()
        for i in range(num_requests):
            result = await make_request(client, i)
            print(f"  Request {result['id']}: {result['time']:.3f}s - {result['backend']}")
        seq_total = time.time() - seq_start
        print(f"Total: {seq_total:.3f}s\n")

        # Concurrent
        print("[2] Concurrent Requests")
        conc_start = time.time()
        tasks = [make_request(client, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        conc_total = time.time() - conc_start

        for r in results:
            print(f"  Request {r['id']}: {r['time']:.3f}s - {r['backend']}")
        print(f"Total: {conc_total:.3f}s\n")

        # Analysis
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Sequential: {seq_total:.3f}s")
        print(f"Concurrent: {conc_total:.3f}s")
        print(f"Speedup: {seq_total/conc_total:.2f}x")

        npu_count = sum(1 for r in results if r['backend'] == 'npu')
        print(f"\nNPU requests: {npu_count}/{num_requests}")

        if conc_total < seq_total * 0.8 and npu_count >= num_requests - 1:
            print("\n[PASS] Concurrent processing is working!")
        else:
            print("\n[INFO] Some optimization may be needed")

        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_concurrent())
