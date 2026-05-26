<div align="center">

# Local RAG Workbench

**A fully local Retrieval-Augmented Generation pipeline — zero cloud dependencies.**

Index your documents. Query them with TF-IDF retrieval.
Synthesise answers with **llama.cpp** or **Ollama** — entirely on your machine.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## What It Does

Local RAG Workbench wires together the full RAG stack — document loading,
text chunking, vector indexing, similarity retrieval, and optional LLM synthesis —
in a single self-contained project you can run in two commands.

Drop `.md` or `.txt` files in a folder, ask a question, get ranked context back
in milliseconds. Enable an LLM backend to synthesise a natural-language answer
from that context. No OpenAI API key. No internet connection. No GPU required.

```
You                  Backend (FastAPI + Python)              LLM (optional)
 │                          │                                     │
 │── "What is RAG?" ───────▶│── TF-IDF cosine similarity ──▶ top chunks
 │                          │── build RAG prompt ───────────────▶│
 │◀─ synthesised answer ────│◀─ generated text ─────────────────│
```

---

## Feature Highlights

| Feature | Detail |
|---|---|
| **Retrieval engine** | TF-IDF + cosine similarity via scikit-learn — no vector DB, no embeddings model |
| **Chunking** | 1 000-char chunks with 175-char overlap; preserves sentence context at boundaries |
| **LLM backends** | llama.cpp (GGUF) and Ollama — pluggable, switchable via one env var |
| **Retrieval-only mode** | Works with zero LLM config — returns ranked context immediately |
| **REST API** | Five clean FastAPI endpoints with CORS, lifespan management, and OpenAPI docs |
| **React UI** | Two-column responsive workbench: query, answer, document list, add docs, history |
| **Single runner** | `run.sh` starts backend + UI together on Linux and macOS |
| **Document ingestion** | Add docs via UI paste, REST API, or drop files in the data directory |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        run.sh (Linux / macOS)                   │
│              ./run.sh [all | backend | ui | install-*]          │
└────────────────────┬───────────────────────┬────────────────────┘
                     │                       │
          ┌──────────▼──────────┐   ┌────────▼────────┐
          │  Backend (port 8000)│   │  UI (port 5173) │
          │  FastAPI + uvicorn  │   │  React + Vite   │
          └──────────┬──────────┘   └─────────────────┘
                     │
          ┌──────────▼──────────────────────────────┐
          │              app/                        │
          │  ┌──────────┐  ┌──────────────────────┐ │
          │  │config.py │  │      main.py          │ │
          │  │ .env     │  │  5 REST endpoints     │ │
          │  └──────────┘  └──────────┬───────────┘ │
          │                           │              │
          │  ┌────────────────────────▼────────────┐ │
          │  │          rag_loader.py               │ │
          │  │  _load_documents()  → .md / .txt     │ │
          │  │  _chunk_text()      → 1000-char chunks│ │
          │  │  reindex()          → TF-IDF matrix  │ │
          │  │  _retrieve()        → cosine sim top-k│ │
          │  │  query()            → context or LLM │ │
          │  └────────────────────┬────────────────┘ │
          │                       │ use_llm=True      │
          │         ┌─────────────▼─────────────┐    │
          │         │      LLM_BACKEND env var   │    │
          │         └──────┬──────────┬──────────┘    │
          │                │          │                │
          │   ┌────────────▼──┐  ┌────▼─────────────┐ │
          │   │ llm_runner.py │  │ ollama_runner.py  │ │
          │   │  llama-server │  │   Ollama API      │ │
          │   │  subprocess   │  │   /api/generate   │ │
          │   └───────────────┘  └───────────────────┘ │
          └─────────────────────────────────────────────┘

  Data layer
  ──────────
  backend/data/          ← .md and .txt files (source of truth)
  backend/vector_db_cache/  ← TF-IDF index (rebuilt on startup)
```

---

## Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build and dev server |
| Ollama | any | Optional LLM synthesis (easiest path) |
| llama.cpp | built from source | Optional LLM synthesis (GGUF models) |

---

## Quick Start

```bash
# Clone the project
git clone <repo-url> && cd RAGFlow

# Start everything (backend + UI) in one command
./run.sh
```

| Service | URL |
|---|---|
| React UI | http://localhost:5173 |
| FastAPI backend | http://127.0.0.1:8000 |
| Interactive API docs | http://127.0.0.1:8000/docs |

Press **Ctrl+C** to stop both services.

> On first run, `backend/.env` is created automatically from `.env.example`.
> Retrieval-only mode works immediately with no further configuration.

---

## run.sh Reference

```
Usage:  ./run.sh [command]

  (none) / all      Start backend + UI together
  backend           Backend only     →  http://127.0.0.1:8000
  ui                UI only          →  http://localhost:5173
  install-llama     Clone and build llama.cpp from source
  install-ollama    Install Ollama (Linux: curl script, macOS: brew or curl)
  help              Show this reference
```

---

## Enabling LLM Synthesis

By default `ENABLE_LLM=false`. The workbench runs in **retrieval-only mode**
and returns ranked document chunks instantly — no model required.

To synthesise natural-language answers, enable one of the two LLM backends:

### Option A — Ollama  *(recommended — easiest setup)*

```bash
# 1. Install Ollama
./run.sh install-ollama

# 2. Start the Ollama daemon
ollama serve

# 3. Pull a model (see https://ollama.com/library for the full list)
ollama pull llama3         # ~4 GB — good general purpose
ollama pull mistral        # ~4 GB — strong reasoning
ollama pull phi3           # ~2 GB — fast, low memory

# 4. Set in backend/.env
ENABLE_LLM=true
LLM_BACKEND=ollama
OLLAMA_MODEL=llama3

# 5. Restart the backend
./run.sh backend
```

### Option B — llama.cpp  *(full control, GGUF models)*

```bash
# 1. Build llama-server from source
./run.sh install-llama

# 2. Download a GGUF model
#    Find models at https://huggingface.co/models?search=gguf
#    Example: Meta-Llama-3-8B-Instruct.Q4_K_M.gguf

# 3. Set in backend/.env
ENABLE_LLM=true
LLM_BACKEND=llama_cpp
MODEL_PATH=/path/to/your-model.gguf
LLAMA_SERVER_BIN=/path/to/llama.cpp/build/bin/llama-server

# 4. Restart the backend
./run.sh backend
```

---

## API Reference

All endpoints are under `http://127.0.0.1:8000`. Interactive docs at `/docs`.

### `GET /api/hello` — Health check

```bash
curl http://127.0.0.1:8000/api/hello
```

```json
{
  "status": "ok",
  "message": "Local RAG Workbench backend is running.",
  "llm_backend": "disabled"
}
```

---

### `GET /api/available-documents` — List indexed documents

```bash
curl http://127.0.0.1:8000/api/available-documents
```

```json
{
  "documents": [
    { "source": "sample_notes.md", "chunks": 3 },
    { "source": "architecture.md", "chunks": 7 }
  ]
}
```

---

### `POST /api/docscan` — Query the RAG pipeline

**Retrieval-only** (default):

```bash
curl -X POST http://127.0.0.1:8000/api/docscan \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this project?"}'
```

**With LLM synthesis** (requires `ENABLE_LLM=true`):

```bash
curl -X POST "http://127.0.0.1:8000/api/docscan?usellm=true" \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarise the key features of this workbench."}'
```

```json
{
  "reply": "Top retrieved context:\n\n1. Source: sample_notes.md (score: 0.4231)\n..."
}
```

---

### `POST /api/documents` — Add a document

```bash
curl -X POST http://127.0.0.1:8000/api/documents \
  -H "Content-Type: application/json" \
  -d '{
    "source": "my-notes.md",
    "text": "# Project Notes\n\nThis workbench supports TF-IDF retrieval..."
  }'
```

```json
{ "status": "indexed", "source": "my-notes.md", "chunks": 2 }
```

---

### `POST /api/reindex` — Reindex all documents

Useful after manually adding, editing, or removing files in `backend/data/`.

```bash
curl -X POST http://127.0.0.1:8000/api/reindex
```

```json
{ "status": "reindexed", "documents": 3, "chunks": 14 }
```

---

### Smoke-test all endpoints

```bash
bash scripts/test_api.sh
```

---

## Configuration Reference

`backend/.env` is created from `.env.example` on first run.
Edit it to configure paths, enable the LLM, or switch backends.

### Server

| Variable | Default | Description |
|---|---|---|
| `APP_HOST` | `127.0.0.1` | FastAPI bind host |
| `APP_PORT` | `8000` | FastAPI bind port |
| `DATA_DIR` | `<backend>/data` | Directory scanned for `.md` and `.txt` documents |
| `VECTOR_DB_DIR` | `<backend>/vector_db_cache` | Directory for TF-IDF cache files |

### LLM

| Variable | Default | Description |
|---|---|---|
| `ENABLE_LLM` | `false` | Set `true` to activate LLM synthesis |
| `LLM_BACKEND` | `llama_cpp` | Active backend: `llama_cpp` or `ollama` |

### llama.cpp settings  *(when `LLM_BACKEND=llama_cpp`)*

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | *(empty)* | Absolute path to a `.gguf` model file |
| `LLAMA_SERVER_BIN` | `llama-server` | Binary path or name (must be on PATH if no full path) |
| `LLAMA_HOST` | `127.0.0.1` | llama-server bind host |
| `LLAMA_PORT` | `8080` | llama-server bind port |
| `LLAMA_CONTEXT_SIZE` | `2048` | Token context window |
| `LLAMA_GPU_LAYERS` | `0` | Layers offloaded to GPU (`0` = CPU-only) |
| `LLAMA_THREADS` | `4` | CPU threads for inference |
| `LLAMA_PARALLEL` | `1` | Parallel inference slots |
| `LLAMA_USE_MLOCK` | `false` | Lock model weights in RAM |

### Ollama settings  *(when `LLM_BACKEND=ollama`)*

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `127.0.0.1` | Ollama service host |
| `OLLAMA_PORT` | `11434` | Ollama service port |
| `OLLAMA_MODEL` | `llama3` | Model identifier — run `ollama list` to see installed models |

---

## How the RAG Pipeline Works

```
Document ingestion
──────────────────
  backend/data/*.md, *.txt
        │
        ▼
  _load_documents()         reads files, returns {source, text} pairs
        │
        ▼
  _chunk_text()             splits each document into 1 000-char chunks
                            with 175-char overlap to preserve boundary context
        │
        ▼
  TfidfVectorizer.fit()     builds vocabulary + IDF weights over all chunks
  tfidf_matrix              sparse (n_chunks × vocab_size) matrix

Query execution
───────────────
  user question
        │
        ▼
  TfidfVectorizer.transform()   vectorise the question
        │
        ▼
  cosine_similarity()           score every chunk
        │
        ▼
  top-k chunks (k=5)            ranked by score, score > 0 only

  if use_llm=False  →  return formatted context string
  if use_llm=True   →  build RAG prompt → llm_runner.query() → answer
```

---

## Project Structure

```
RAGFlow/
│
├── run.sh                          Cross-platform entry point (Linux + macOS)
├── requirements.txt                Root Python deps (mirrors backend/)
├── .gitignore
├── README.md
├── SPEC.md                         Full project specification
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 FastAPI app, lifespan, 5 API endpoints
│   │   ├── config.py               Settings dataclass + .env loader
│   │   ├── llm_runner.py           llama-server subprocess manager
│   │   ├── ollama_runner.py        Ollama REST API client
│   │   └── rag_loader.py           TF-IDF pipeline: load → chunk → index → retrieve
│   ├── data/
│   │   └── sample_notes.md         Starter document (indexed on first run)
│   ├── vector_db_cache/
│   │   └── .gitkeep
│   ├── requirements.txt
│   └── .env.example
│
├── ui/
│   ├── src/
│   │   ├── main.jsx                Single-page React app (all state + panels)
│   │   └── styles.css              Light workbench theme (no Tailwind)
│   ├── index.html
│   ├── package.json                React 18 + Vite 5
│   ├── vite.config.js
│   └── .env.example
│
├── scripts/
│   ├── run_backend.sh              Venv setup + uvicorn
│   ├── run_ui.sh                   npm install + vite dev
│   ├── install_llama_cpp.sh        git clone + cmake build
│   └── test_api.sh                 curl smoke tests for all endpoints
│
└── source_archived/                Legacy prototype (LangChain + FAISS + OpenAI)
    ├── db_manager.py               Original DBManager — reference only
    ├── app.py                      Original FastAPI wiring — reference only
    ├── apiv1.py                    Original /api/v1/query route — reference only
    └── main.py                     Original script entry — reference only
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API server | FastAPI + uvicorn | Async, fast, automatic OpenAPI docs |
| Retrieval | scikit-learn TF-IDF | No GPU, no embedding model, instant startup |
| Similarity | NumPy cosine similarity | Vectorised, runs in microseconds |
| LLM (option A) | Ollama | One-command install, huge model library |
| LLM (option B) | llama.cpp / llama-server | GGUF models, full hardware control |
| Config | python-dotenv | Twelve-factor app config from .env |
| Frontend | React 18 + Vite 5 | Fast dev server, no build complexity |
| Styling | Plain CSS | No Tailwind, no component library |

---

## LLM Backend Comparison

| | Ollama | llama.cpp |
|---|---|---|
| Setup effort | Install + `ollama pull` | Build from source + download GGUF |
| Model format | Ollama library | Any GGUF |
| Process management | External daemon | Managed by app (subprocess) |
| GPU support | Automatic | Configurable layers |
| Recommended for | Quick start, experimentation | Fine-grained hardware control |
| Config key | `LLM_BACKEND=ollama` | `LLM_BACKEND=llama_cpp` |

---

## Development Notes

### Adding documents without the UI

Drop any `.md` or `.txt` file into `backend/data/` and hit the reindex endpoint:

```bash
cp my-document.md backend/data/
curl -X POST http://127.0.0.1:8000/api/reindex
```

### Extending supported file types

Add extensions to the `supported_exts` set in `RAGLoader._load_documents()`:

```python
supported_exts = {".md", ".txt", ".rst", ".log"}
```

### Tuning chunk size

Edit the constants in `RAGLoader._chunk_text()`:

```python
chunk_size = 1000   # characters per chunk  (spec range: 800–1200)
overlap    = 175    # overlap per boundary   (spec range: 150–200)
```

Larger chunks preserve more context per result; smaller chunks improve
retrieval precision on short, specific questions.

### Interactive API docs

FastAPI generates Swagger UI automatically:

```
http://127.0.0.1:8000/docs      Swagger UI
http://127.0.0.1:8000/redoc     ReDoc
http://127.0.0.1:8000/openapi.json  Raw OpenAPI schema
```

---

## Roadmap

The following features are planned for future iterations:

- [ ] File upload from the UI (drag-and-drop)
- [ ] PDF parsing support
- [ ] Markdown rendering in the answer panel
- [ ] Source citation cards alongside answers
- [ ] Streaming LLM responses
- [ ] SQLite-backed persistent query history
- [ ] Document delete and update endpoints
- [ ] Hybrid retrieval combining TF-IDF and dense embeddings
- [ ] ChromaDB or FAISS vector store backend
- [ ] Docker Compose setup for one-command deployment
- [ ] Configurable chunk size from the UI

---

<div align="center">

Built for developers who want to understand and control their RAG pipeline
from document loading to answer synthesis — without touching a cloud API.

</div>
