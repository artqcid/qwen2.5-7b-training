"""RAG-specific test fixtures."""
import pytest
import yaml
import subprocess
import time
import httpx
from pathlib import Path
import sys
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from rag_client import RAGClient


@pytest.fixture(scope="session")
def qdrant_server():
    """Ensure Qdrant server is running (native from C:\\qdrant)."""
    qdrant_url = "http://localhost:6333"
    qdrant_dir = Path("C:/qdrant")
    qdrant_binary = qdrant_dir / "qdrant.exe"
    
    # Check if Qdrant is already running
    try:
        response = httpx.get(f"{qdrant_url}/collections", timeout=2.0)
        if response.status_code == 200:
            print("\n✓ Qdrant already running")
            yield qdrant_url
            return
    except:
        pass
    
    # Start Qdrant from C:\qdrant
    if not qdrant_binary.exists():
        pytest.skip(
            f"Qdrant binary not found at {qdrant_binary}. "
            "Please ensure Qdrant is installed in C:\\qdrant"
        )
    
    print(f"\n→ Starting Qdrant from {qdrant_dir}...")
    
    try:
        # Start Qdrant with proper working directory for configs
        process = subprocess.Popen(
            [str(qdrant_binary)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(qdrant_dir),  # Important: use C:\qdrant as working dir for configs
            creationflags=subprocess.CREATE_NO_WINDOW  # No console window
        )
        
        # Wait for Qdrant to be ready (max 30 seconds)
        for i in range(30):
            try:
                response = httpx.get(f"{qdrant_url}/collections", timeout=2.0)
                if response.status_code == 200:
                    print(f"✓ Qdrant started successfully")
                    break
            except:
                if process.poll() is not None:
                    # Process exited, read error
                    stderr = process.stderr.read().decode('utf-8', errors='ignore')
                    pytest.skip(f"Qdrant process exited unexpectedly: {stderr}")
                time.sleep(1)
        else:
            process.terminate()
            pytest.skip("Qdrant did not start in time (30s timeout)")
        
        yield qdrant_url
        
        # Cleanup: Stop Qdrant gracefully
        print("\n→ Stopping Qdrant...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✓ Qdrant stopped")
        except subprocess.TimeoutExpired:
            process.kill()
            print("⚠ Qdrant force killed")
        
    except Exception as e:
        pytest.skip(f"Could not start Qdrant: {e}")


@pytest.fixture(scope="session")
def embedding_server():
    """Start Embedding Server if not running."""
    endpoint = "http://127.0.0.1:8001"
    
    # Check if already running
    try:
        response = httpx.get(f"{endpoint}/health", timeout=2.0)
        if response.status_code == 200:
            print("\n✓ rag_server):
    """Create RAG client for testing."""
    endpoint = config.get("rag", {}).get("endpoint", "http://127.0.0.1:8002")
    timeout = config.get("rag", {}).get("timeout", 60)
    
    client = RAGClient(endpoint=endpoint, timeout=timeout)
    
    # Verify RAG server is healthyrver...")
    embedding_script = Path(__file__).parent.parent.parent.parent.parent / "embedding-server-misc" / "start.ps1"
    
    if not embedding_script.exists():
        pytest.skip(f"Embedding server script not found: {embedding_script}")
    
    try:
        process = subprocess.Popen(
            ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(embedding_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Wait for server to be ready
        for i in range(60):
            try:
                response = httpx.get(f"{endpoint}/health", timeout=2.0)
                if response.status_code == 200:
                    print("✓ Embedding Server started")
                    break
            except:
                if process.poll() is not None:
                    pytest.skip("Embedding Server exited unexpectedly")
                time.sleep(1)
        else:
            process.terminate()
            pytest.skip("Embedding Server did not start in time")
        
        yield endpoint
        
        # Cleanup
        print("\n→ Stopping Embedding Server...")
        subprocess.run(
            ["pwsh", "-NoProfile", "-Command", 
             "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*embedding_server*' } | Stop-Process -Force"],
            capture_output=True
        )
        
    except Exception as e:
        pytest.skip(f"Could not start Embedding Server: {e}")


@pytest.fixture(scope="session")
def llm_server():
    """Start LLM Server if not running."""
    endpoint = "http://127.0.0.1:8080/health"
    
    # Check if already running
    try:
        response = httpx.get(endpoint, timeout=2.0)
        if response.status_code == 200:
            print("\n✓ LLM Server already running")
            yield "http://127.0.0.1:8080"
            return
    except:
        pass
    
    # Start LLM Server
    print("\n→ Starting LLM Server...")
    llm_script = Path("C:/Users/marku/.continue/llama-vscode-autostart.ps1")
    
    if not llm_script.exists():
        pytest.skip(f"LLM server script not found: {llm_script}")
    
    try:
        process = subprocess.Popen(
            ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(llm_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Wait for server to be ready
        for i in range(60):
            try:
                response = httpx.get(endpoint, timeout=2.0)
                if response.status_code == 200:
                    print("✓ LLM Server started")
                    break
            except:
                if process.poll() is not None:
                    pytest.skip("LLM Server exited unexpectedly")
                time.sleep(1)
        else:
            process.terminate()
            pytest.skip("LLM Server did not start in time")
        
        yield "http://127.0.0.1:8080"
        
        # Cleanup
        print("\n→ Stopping LLM Server...")
        subprocess.run(
            ["pwsh", "-NoProfile", "-Command", 
             "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"],
            capture_output=True
        )
        
    except Exception as e:
        pytest.skip(f"Could not start LLM Server: {e}")


@pytest.fixture(scope="session")
def rag_server(embedding_server, llm_server, qdrant_server):
    """Start RAG Server if not running (depends on Embedding, LLM, Qdrant)."""
    endpoint = "http://127.0.0.1:8002"
    
    # Check if already running
    try:
        response = httpx.get(f"{endpoint}/health", timeout=2.0)
        if response.status_code == 200:
            print("\n✓ RAG Server already running")
            yield endpoint
            return
    except:
        pass
    
    # Start RAG Server
    print("\n→ Starting RAG Server...")
    rag_script = Path(__file__).parent.parent.parent.parent.parent / "rag-server-misc" / "start.ps1"
    
    if not rag_script.exists():
        pytest.skip(f"RAG server script not found: {rag_script}")
    
    try:
        process = subprocess.Popen(
            ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(rag_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Wait for server to be ready
        for i in range(60):
            try:
                response = httpx.get(f"{endpoint}/health", timeout=2.0)
                if response.status_code == 200:
                    print("✓ RAG Server started")
                    break
            except:
                if process.poll() is not None:
                    pytest.skip("RAG Server exited unexpectedly")
                time.sleep(2)
        else:
            process.terminate()
            pytest.skip("RAG Server did not start in time")
        
        yield endpoint
        
        # Cleanup
        print("\n→ Stopping RAG Server...")
        subprocess.run(
            ["pwsh", "-NoProfile", "-Command", 
             "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*rag_server*' } | Stop-Process -Force"],
            capture_output=True
        )
        
    except Exception as e:
        pytest.skip(f"Could not start RAG Server: {e}")


@pytest.fixture(scope="session")
def rag_smoke_config(config):
    """Load RAG smoke test configuration."""
    rag_config_path = Path(__file__).parent / "rag_smoke_config.yaml"
    with open(rag_config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def rag_client(config, qdrant_server):
    """Create RAG client for testing."""
    endpoint = config.get("rag", {}).get("endpoint", "http://127.0.0.1:8002")
    timeout = config.get("rag", {}).get("timeout", 60)
    
    client = RAGClient(endpoint=endpoint, timeout=timeout)
    
    # Check if RAG server is running
    try:
        health = client.health()
        print(f"\n✓ RAG Server connected: {health.get('status')}")
    except Exception as e:
        pytest.skip(f"RAG server not available at {endpoint}: {e}")
    
    yield client
    client.close()


@pytest.fixture(scope="function")
def clean_test_collection(rag_client, rag_smoke_config):
    """Ensure test collection is clean before and after each test."""
    collection = rag_smoke_config.get("collection", "test_rag_vue")
    
    # Cleanup before test
    try:
        rag_client.delete_collection(collection)
    except:
        pass  # Collection might not exist
    
    yield collection
    
    # Cleanup after test
    try:
        rag_client.delete_collection(collection)
        print(f"\n✓ Test collection '{collection}' cleaned up")
    except Exception as e:
        print(f"\n⚠ Could not delete test collection: {e}")
