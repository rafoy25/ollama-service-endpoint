"""
Quick setup script for NPU embedding service
Run this on first setup or when deploying to new server
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run command and handle errors"""
    print(f"\n[{description}]")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(e.stderr)
        return False


def main():
    print("=" * 70)
    print("Intel NPU Embedding Service - Setup Script")
    print("=" * 70)

    # Step 1: Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10+ required")
        return False

    # Step 2: Install dependencies
    if not run_command(
        "pip install -r requirements-npu.txt",
        "Installing dependencies"
    ):
        print("\nFailed to install dependencies. Try manually:")
        print("  pip install -r requirements-npu.txt")
        return False

    # Step 3: Check NPU availability
    print("\n" + "=" * 70)
    print("Checking for NPU/iGPU...")
    print("=" * 70)

    if not run_command("python check_npu.py", "Checking devices"):
        return False

    # Step 4: Convert model if not exists
    model_path = Path("./models/mxbai-embed-large-ov/model.xml")

    if not model_path.exists():
        print("\n" + "=" * 70)
        print("Converting embedding model to OpenVINO format...")
        print("This may take 5-10 minutes on first run")
        print("=" * 70)

        if not run_command("python convert_model_simple.py", "Converting model"):
            print("\nModel conversion failed. Try manually:")
            print("  python convert_model_simple.py")
            return False
    else:
        print(f"\n[INFO] Model already exists at {model_path}")

    # Step 5: Test embedding service
    print("\n" + "=" * 70)
    print("Testing NPU embedding service...")
    print("=" * 70)

    if not run_command("python test_npu_embeddings.py", "Testing embeddings"):
        print("\nEmbedding test failed. Check logs above.")
        return False

    # Success!
    print("\n" + "=" * 70)
    print("SETUP COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Start FastAPI server:")
    print("   python main.py")
    print()
    print("2. Test the API:")
    print("   python test_integrated_api.py")
    print()
    print("3. Check health endpoint:")
    print("   curl http://localhost:8000/api/health")
    print()
    print("4. Read deployment guide:")
    print("   NPU_DEPLOYMENT_GUIDE.md")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
