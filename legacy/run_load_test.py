#!/usr/bin/env python3
"""
Locust Load Testing Script for FastAPI Concurrency

Usage:
1. First install requirements: pip install -r requirements-locust.txt
2. Start your FastAPI server: python main.py
3. Run this script: python run_load_test.py
4. Open browser to: http://localhost:8089
5. Configure test parameters in the web UI

Test scenarios:
- FastAPIUser: Mixed workload (chat + embeddings + health checks)
- HeavyUser: Intensive operations to test concurrency
- ChatOnlyUser: Chat-focused users
- EmbeddingOnlyUser: Embedding-focused users
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Locust Load Test for FastAPI Concurrency")
    print("=" * 50)
    print("📊 Web UI will be available at: http://localhost:8089")
    print("🎯 Target API: http://localhost:8000")
    print("⚠️  Make sure your FastAPI server is running!")
    print("=" * 50)
    
    # Check if locustfile exists
    if not os.path.exists("locustfile.py"):
        print("❌ Error: locustfile.py not found!")
        sys.exit(1)
    
    try:
        # Run Locust with web UI
        cmd = [
            "locust", 
            "--host=http://localhost:8000",
            "--web-host=0.0.0.0",
            "--web-port=8089"
        ]
        
        print(f"🔥 Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Locust: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Load test stopped by user")
    except FileNotFoundError:
        print("❌ Error: Locust not installed!")
        print("💡 Install with: pip install -r requirements-locust.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()