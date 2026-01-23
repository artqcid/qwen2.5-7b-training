# Qwen2.5-7B Training Project - Service Integration Guide

## Architecture

```
Chat Server (Port 8000)            Embedding Server (Port 8001)
  Qwen2.5-7B (GPU)                  nomic-embed-text (CPU)
  [████████] 4-5GB VRAM             [██] 600-800MB RAM
  llama.cpp server                   embedding-server-misc (submodule)
```

## Starting Services

### 1. Embedding Server (for Continue IDE)

**Automatic setup with dependencies:**
```powershell
.\scripts\start_services.ps1 -InstallDeps
```

**Manual start (after first installation):**
```powershell
.\scripts\start_services.ps1
```

The embedding server will start on `http://localhost:8001` and can be used by:
- Continue IDE for `@codebase` semantic search
- Future RAG integration in `web_mcp.py`

### 2. Chat Server (Qwen2.5-7B)

The main chat server should be started **separately** in another terminal:

```powershell
# Using your existing llama.cpp setup
cd C:\llama
.\server -m models\qwen2.5-7b-chat.gguf --port 8000
```

> **Note**: Both services can run simultaneously. The embedding server uses minimal CPU resources and won't affect the GPU-based chat server.

## Continue IDE Configuration

Once the embedding server is running, configure Continue to use it:

```json
// ~/.continue/config.json
{
  "models": [
    {
      "title": "Qwen2.5-7B",
      "provider": "llamacpp",
      "model": "qwen2.5-7b",
      "apiBase": "http://localhost:8000/v1"
    }
  ],
  "embeddingsProvider": {
    "provider": "openai",
    "apiBase": "http://localhost:8001/v1",
    "model": "nomic-embed-text-v1.5",
    "apiKey": "dummy"
  }
}
```

Now `@codebase` will use your local embedding server for semantic code search!

## Project Structure

```
qwen2.5-7b-training/
├── scripts/
│   └── start_services.ps1          # Project-specific service orchestration
├── python/
│   ├── modelTraining.py            # Training logic
│   ├── model4bitloader.py
│   ├── createDataSet.py
│   └── dataset_juce8_complete_full/
├── embedding-server-misc/          # Git Submodule (CPU embeddings)
│   ├── embedding_server/
│   ├── setup.py
│   └── requirements.txt
└── llama_config.json
```

## Important Notes

### Generalization of embedding-server-misc

The `embedding-server-misc` submodule is **kept generic** for reuse across projects:
- No training-specific code
- No project-specific configuration
- Can be used by any project that needs embeddings
- Updated independently via `git submodule update`

### Project-Specific Integration

Any training-specific integrations belong in this project:
- `scripts/start_services.ps1` - orchestrates service startup
- Future: RAG integration in training pipeline
- Future: Model evaluation with embeddings

### Working with Submodules

```bash
# Clone project with submodule
git clone --recurse-submodules https://github.com/artqcid/qwen2.5-7b-training.git

# Update submodule to latest
cd qwen2.5-7b-training
git submodule update --remote embedding-server-misc
git commit -am "Update embedding-server-misc submodule"
git push

# Or directly update in submodule
cd embedding-server-misc
git pull origin main
cd ..
git add embedding-server-misc
git commit -m "Update embedding-server-misc to latest"
```

## Troubleshooting

### Model not found
```
FileNotFoundError: Model not found: d:\AI-Models\embedding\nomic\nomic-embed-text-v1.5.Q5_K_M.gguf
```
Download the model or update `EMBEDDING_MODEL_PATH` in `embedding-server-misc/embedding_server/config.py`

### Connection refused on port 8001
```
RuntimeError: Connection refused to http://localhost:8001
```
Make sure embedding server is running:
```powershell
.\scripts\start_services.ps1
```

### Port already in use
Change port in script:
```powershell
$env:EMBEDDING_PORT = "8002"
.\scripts\start_services.ps1
```

Then update Continue config to use port `8002`.
