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


def cleanup_duplicate_processes(process_pattern: str, service_name: str) -> int:
    """
    Find and stop DUPLICATE Python processes matching a pattern.
    Uvicorn/Python servers may spawn worker processes, so we consider
    2 processes as normal (main + worker). Only stop if there are 3+ processes.
    
    Args:
        process_pattern: Pattern to match in command line (e.g., 'embedding_server')
        service_name: Name for logging purposes
        
    Returns:
        Number of processes stopped
    """
    if sys.platform != "win32":
        return 0
        
    stopped = 0
    try:
        # Get all python processes with their command lines
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {{ "
             f"$cmdline = (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\" -ErrorAction SilentlyContinue).CommandLine; "
             f"if ($cmdline -like '*{process_pattern}*') {{ $_.Id }} }}"],
            capture_output=True, text=True, timeout=10
        )
        
        pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip().isdigit()]
        
        # Consider 1-2 processes as normal (main process + optional worker)
        # Only stop if there are 3+ processes (true duplicates from multiple starts)
        if len(pids) > 2:
            # Stop half of them (keeping one server instance = 2 processes)
            to_stop = pids[2:]  # Keep first 2, stop the rest
            print(f"\n[WARN] Found {len(pids)} {service_name} processes - stopping {len(to_stop)} duplicate(s)...")
            for pid in to_stop:
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"],
                        timeout=5
                    )
                    print(f"  Stopped duplicate PID {pid}")
                    stopped += 1
                except Exception as e:
                    print(f"  Failed to stop PID {pid}: {e}")
            
            if stopped > 0:
                time.sleep(2)  # Wait for ports to be released
        elif len(pids) > 0:
            print(f"[OK] {service_name}: {len(pids)} process(es) running")
                
    except Exception as e:
        print(f"  Warning: Could not check for duplicate {service_name} processes: {e}")
    
    return stopped


@pytest.fixture(scope="session", autouse=True)
def cleanup_duplicate_servers():
    """Auto-cleanup duplicate server processes before tests run."""
    cleanup_duplicate_processes("embedding_server", "Embedding Server")
    cleanup_duplicate_processes("rag_server", "RAG Server")
    yield


@pytest.fixture(scope="session")
def qdrant_server():
    """Ensure Qdrant server is running (native from C:\\qdrant)."""
    qdrant_url = "http://localhost:6333"
    qdrant_dir = Path("C:/qdrant")
    qdrant_binary = qdrant_dir / "qdrant.exe"
    
    # Check if Qdrant is already running (disable HTTP/2)
    try:
        with httpx.Client(http2=False, timeout=5.0) as client:
            response = client.get(f"{qdrant_url}/collections")
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
            cwd=str(qdrant_dir),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Wait for Qdrant to be ready (max 30 seconds)
        for i in range(30):
            try:
                with httpx.Client(http2=False, timeout=5.0) as client:
                    response = client.get(f"{qdrant_url}/collections")
                if response.status_code == 200:
                    print(f"✓ Qdrant started successfully")
                    break
            except:
                if process.poll() is not None:
                    stderr = process.stderr.read().decode("utf-8", errors="ignore")
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
    """Ensure Embedding Server is running."""
    endpoint = "http://127.0.0.1:8001"
    
    # Check if running
    try:
        with httpx.Client(http2=False, timeout=5.0) as client:
            response = client.get(f"{endpoint}/health")
        if response.status_code == 200:
            print("\n✓ Embedding Server running")
            yield endpoint
            return
    except:
        pass
    
    pytest.skip(
        "Embedding Server not running on port 8001. "
        "Please start it manually: Tasks -> 'Start Embedding Server'"
    )


@pytest.fixture(scope="session")
def llm_server():
    """Ensure LLM Server is running."""
    endpoint = "http://127.0.0.1:8080/health"
    
    # Check if running
    try:
        with httpx.Client(http2=False, timeout=5.0) as client:
            response = client.get(endpoint)
        if response.status_code == 200:
            print("\n✓ LLM Server running")
            yield "http://127.0.0.1:8080"
            return
    except:
        pass
    
    pytest.skip(
        "LLM Server not running on port 8080. "
        "Please start it manually: Tasks -> 'Start Llama.cpp Server'"
    )


@pytest.fixture(scope="session")
def rag_server(embedding_server, llm_server, qdrant_server):
    """Ensure RAG Server is running (depends on Embedding, LLM, Qdrant)."""
    endpoint = "http://127.0.0.1:8002"
    
    # Check if running
    try:
        with httpx.Client(http2=False, timeout=5.0) as client:
            response = client.get(f"{endpoint}/health")
        if response.status_code == 200:
            print("\n✓ RAG Server running")
            yield endpoint
            return
    except:
        pass
    
    pytest.skip(
        "RAG Server not running on port 8002. "
        "Please start all servers first: Tasks -> 'Start All Servers', "
        "then start RAG server manually"
    )


@pytest.fixture(scope="session")
def rag_smoke_config(config):
    """Load RAG smoke test configuration."""
    rag_config_path = Path(__file__).parent / "rag_smoke_config.yaml"
    with open(rag_config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def rag_client(config, rag_server):
    """Create RAG client for testing."""
    endpoint = config.get("rag", {}).get("endpoint", "http://127.0.0.1:8002")
    timeout = config.get("rag", {}).get("timeout", 60)
    
    client = RAGClient(endpoint=endpoint, timeout=timeout)
    
    # Verify RAG server is healthy
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
