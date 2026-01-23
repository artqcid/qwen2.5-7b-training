# Embedding Server Misc

A fast, CPU-efficient embedding server for Continue IDE, RAG systems, and other AI projects. Built with FastAPI and llama-cpp-python.

**Model**: nomic-embed-text-v1.5 (Q5_K_M quantized)  
**Hardware**: CPU-only (no VRAM required)  
**Performance**: ~200-300ms per embedding

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/artqcid/embedding-server-misc.git
cd embedding-server-misc

# Install in development mode
pip install -e .
```

### Run Server

```bash
# Option 1: Using installed command
embedding-server

# Option 2: Using Python module
python -m embedding_server

# Option 3: Manual with environment variables
$env:EMBEDDING_MODEL_PATH = "d:\AI-Models\embedding\nomic\nomic-embed-text-v1.5.Q5_K_M.gguf"
python -m embedding_server
```

Server will start on `http://localhost:8001`

## API Usage

### Generate Embeddings

**Request:**
```bash
curl -X POST http://localhost:8001/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "model": "nomic-embed-text-v1.5"}'
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.123, -0.456, ...]
    }
  ],
  "model": "nomic-embed-text-v1.5",
  "usage": {"prompt_tokens": 2, "total_tokens": 2}
}
```

### Check Health

```bash
curl http://localhost:8001/health
```

### List Models

```bash
curl http://localhost:8001/models
```

## Python Client

### Async Usage

```python
from embedding_server.client import EmbeddingClient

async with EmbeddingClient("http://localhost:8001") as client:
    # Single text
    embeddings = await client.embed("Hello world")
    
    # Multiple texts
    embeddings = await client.embed([
        "JUCE audio documentation",
        "Vue.js framework guide",
        "React hooks tutorial"
    ])
    
    # Check health
    health = await client.health()
    print(health)
```

### Sync Usage

```python
from embedding_server.client import SyncEmbeddingClient

client = SyncEmbeddingClient("http://localhost:8001")
embeddings = client.embed("Hello world")
print(embeddings)
client.close()
```

### Integration with web_mcp.py

```python
# In your web_mcp.py
from embedding_server.client import EmbeddingClient

async def create_rag_index(urls: List[str]):
    """Create vector index for RAG using embeddings."""
    async with EmbeddingClient() as client:
        chunks = []  # Your URL contents split into chunks
        embeddings = await client.embed(chunks)
        # Store in FAISS/ChromaDB/Pinecone
        ...
```

## Continue IDE Configuration

Add to your Continue `config.json`:

```json
{
  "embeddingsProvider": {
    "provider": "openai",
    "apiBase": "http://localhost:8001/v1",
    "model": "nomic-embed-text-v1.5",
    "apiKey": "dummy"
  }
}
```

Now `@codebase` will use this embedding server for semantic code search!

## Configuration

Use environment variables to customize:

```powershell
$env:EMBEDDING_MODEL_PATH = "path/to/model.gguf"
$env:EMBEDDING_MODEL_NAME = "nomic-embed-text-v1.5"
$env:EMBEDDING_CTX_SIZE = "256"
$env:EMBEDDING_VERBOSE = "true"
$env:EMBEDDING_HOST = "127.0.0.1"
$env:EMBEDDING_PORT = "8001"
```

Or modify `embedding_server/config.py` directly.

## Resource Usage

- **RAM**: ~600-800MB (model + inference)
- **CPU**: Moderate usage during embedding (~2-4 cores)
- **VRAM**: None (CPU-only!)

## Troubleshooting

### Model not found
```
FileNotFoundError: Model not found: d:\AI-Models\embedding\nomic\nomic-embed-text-v1.5.Q5_K_M.gguf
```
Download the model or update `EMBEDDING_MODEL_PATH` environment variable.

### Connection refused
```
RuntimeError: Embedding request failed: Connection refused
```
Make sure server is running: `python -m embedding_server`

### Slow embeddings
- Reduce `EMBEDDING_CTX_SIZE` (default: 256)
- Increase `n_threads` in config.py
- Use a more powerful CPU

## Architecture

```
Chat Server (8000)        Embedding Server (8001)
  Qwen2.5-7B GPU            nomic-embed-text CPU
  [████████] 4-5GB VRAM     [██] 600-800MB RAM
```

Independent services = no resource conflicts!

## Development

```bash
# Run tests
pytest tests/

# Run with debug logging
$env:EMBEDDING_VERBOSE = "true"
python -m embedding_server
```

## License

MIT

## Related Projects

- [web_mcp.py](https://github.com/artqcid/mcp-misc) - Web context provider for MCP
- [Continue IDE](https://continue.dev) - AI code assistant
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - CPU inference engine
