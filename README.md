# Local RAG Workbench

A local Retrieval-Augmented Generation tool that indexes documents from a local folder,
retrieves relevant chunks for a user question, and optionally sends the retrieved context
to a local LLM for answer synthesis.

Supported LLM backends: **llama.cpp** (GGUF models) and **Ollama**.
No cloud APIs required.

---

## Requirements

- Python 3.10+
- Node.js 18+
- (Optional) llama.cpp **or** Ollama for LLM synthesis

---

## Quick Start

```bash
./run.sh
```

This starts both the backend (`http://127.0.0.1:8000`) and the React UI (`http://localhost:5173`) together.
Press **Ctrl+C** to stop both.

---

## run.sh Commands

```
./run.sh                  start backend + UI together (default)
./run.sh all              same as above
./run.sh backend          backend only
./run.sh ui               UI only
./run.sh install-llama    clone and build llama.cpp from source
./run.sh install-ollama   install Ollama (Linux: curl, macOS: brew or curl)
./run.sh help             show usage
```

Works on **Linux** and **macOS**.

---

## Enabling Local LLM Synthesis

By default `ENABLE_LLM=false` — retrieval-only mode works with no model installed.

### Option A — Ollama (easiest)

```bash
# 1. Install Ollama
./run.sh install-ollama

# 2. Start the Ollama service
ollama serve

# 3. Pull a model
ollama pull llama3

# 4. Edit backend/.env
ENABLE_LLM=true
LLM_BACKEND=ollama
OLLAMA_MODEL=llama3

# 5. Restart
./run.sh backend
```

### Option B — llama.cpp

```bash
# 1. Build llama-server
./run.sh install-llama

# 2. Edit backend/.env
ENABLE_LLM=true
LLM_BACKEND=llama_cpp
MODEL_PATH=/path/to/your-model.gguf
LLAMA_SERVER_BIN=/path/to/llama.cpp/build/bin/llama-server

# 3. Restart
./run.sh backend
```

---

## API Endpoints

| Method | Path                      | Description                                  |
|--------|---------------------------|----------------------------------------------|
| GET    | /api/hello                | Backend health check + active LLM backend    |
| GET    | /api/available-documents  | List indexed documents and chunk counts      |
| POST   | /api/docscan?usellm=false | Query RAG (retrieval-only or LLM synthesis)  |
| POST   | /api/documents            | Add a document and reindex                   |
| POST   | /api/reindex              | Reindex all documents in the data directory  |

```bash
# smoke test all endpoints
bash scripts/test_api.sh
```

---

## Configuration Reference

Edit `backend/.env` (created automatically on first run from `.env.example`):

| Variable           | Default       | Description                                     |
|--------------------|---------------|-------------------------------------------------|
| APP_HOST           | 127.0.0.1     | FastAPI bind host                               |
| APP_PORT           | 8000          | FastAPI bind port                               |
| DATA_DIR           | backend/data  | Document input directory                        |
| VECTOR_DB_DIR      | backend/vector_db_cache | TF-IDF cache directory              |
| ENABLE_LLM         | false         | Enable LLM synthesis                            |
| LLM_BACKEND        | llama_cpp     | `llama_cpp` or `ollama`                         |
| MODEL_PATH         | (empty)       | Path to GGUF file (llama_cpp only)              |
| LLAMA_SERVER_BIN   | llama-server  | Path to llama-server binary                     |
| LLAMA_HOST         | 127.0.0.1     | llama-server host                               |
| LLAMA_PORT         | 8080          | llama-server port                               |
| LLAMA_CONTEXT_SIZE | 2048          | Context window size                             |
| LLAMA_GPU_LAYERS   | 0             | GPU layers (0 = CPU only)                       |
| LLAMA_THREADS      | 4             | CPU threads                                     |
| LLAMA_PARALLEL     | 1             | Parallel inference slots                        |
| LLAMA_USE_MLOCK    | false         | Lock model in RAM                               |
| OLLAMA_HOST        | 127.0.0.1     | Ollama host                                     |
| OLLAMA_PORT        | 11434         | Ollama port                                     |
| OLLAMA_MODEL       | llama3        | Ollama model name (`ollama list` to see yours)  |

---

## Project Structure

```
run.sh                      single cross-platform entry point (Linux + macOS)

backend/
  app/
    main.py                 FastAPI entry point, lifespan, and API endpoints
    config.py               Settings class; loads .env and environment variables
    llm_runner.py           LLMRunner — manages llama-server subprocess
    ollama_runner.py        OllamaRunner — queries Ollama REST API
    rag_loader.py           RAGLoader — TF-IDF indexing, chunking, retrieval
  data/                     Source documents to index (.md and .txt)
  vector_db_cache/          TF-IDF index cache directory
  requirements.txt          Python dependencies
  .env.example              Environment variable template

ui/
  src/
    main.jsx                Single-page React UI (all panels and state)
    styles.css              Light minimal workbench theme
  index.html                Vite HTML entry point
  package.json              React 18 + Vite 5 dependencies

scripts/
  run_backend.sh            Backend-only runner (also called by run.sh)
  run_ui.sh                 UI-only runner (also called by run.sh)
  install_llama_cpp.sh      Clone and build llama.cpp
  test_api.sh               Curl-based API smoke tests

source_archived/            Legacy prototype (LangChain + FAISS + OpenAI)
                            Kept for reference — not used by the current app
```
