# Local RAG Workbench

Local RAG Workbench is a local Retrieval-Augmented Generation tool that indexes documents
from a local folder, retrieves relevant chunks for a user question, and optionally sends
the retrieved context to a local llama.cpp model for answer synthesis.

## Purpose

It is used by developers, AI learners, and local LLM experimenters to test RAG pipelines
without depending on cloud APIs.

The problem it solves: without this tool, testing local RAG requires manually wiring
document loading, chunking, retrieval, FastAPI endpoints, local LLM execution, and
UI testing every time.

## How It Works

1. Documents in the data directory are loaded on startup.
2. Text is split into overlapping chunks of approximately 1000 characters with 175-character overlap.
3. A TF-IDF matrix is built over all chunks using scikit-learn.
4. When a question is submitted, cosine similarity scores rank the top matching chunks.
5. The top chunks are returned as formatted context (retrieval-only mode).
6. Optionally, the context and question are sent to a local llama-server for answer synthesis (LLM mode).

## Configuration

Set ENABLE_LLM=false (default) to use retrieval-only mode without any model.
Set ENABLE_LLM=true and provide MODEL_PATH pointing to a GGUF file to enable LLM synthesis.
Set LLAMA_SERVER_BIN to the path of your llama-server binary if it is not on PATH.

## API Endpoints

- GET  /api/hello               — backend health check
- GET  /api/available-documents — list indexed documents and chunk counts
- POST /api/docscan             — query the RAG system (usellm=false|true)
- POST /api/documents           — add a new document and reindex
- POST /api/reindex             — reindex all documents in the data directory

## Stack

- Python 3.10+
- FastAPI and uvicorn for the backend API
- scikit-learn TF-IDF for retrieval
- llama.cpp / llama-server for optional local LLM synthesis
- React and Vite for the frontend UI
