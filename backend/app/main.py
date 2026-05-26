"""
FastAPI application entry point.

Initialises the application at startup (directory setup, LLM runner
selection, RAGLoader construction) and defines the REST API endpoints.

Startup flow
------------
1. Load settings from environment / .env file.
2. Create data and vector-cache directories if they do not exist.
3. If ``ENABLE_LLM=true``, select a runner based on ``LLM_BACKEND``:
   - ``llama_cpp`` → :class:`~app.llm_runner.LLMRunner` (starts a
     llama-server subprocess and waits for it to become healthy).
   - ``ollama`` → :class:`~app.ollama_runner.OllamaRunner` (connects
     to an already-running Ollama service).
4. Initialise :class:`~app.rag_loader.RAGLoader` with the selected
   runner (or ``None`` for retrieval-only mode).
5. Serve the API endpoints listed below.
6. On shutdown, call ``stop_server()`` on the active runner.

Endpoints
---------
GET  /api/hello                  — health check
GET  /api/available-documents    — list indexed documents
POST /api/docscan                — RAG query (retrieval-only or LLM)
POST /api/documents              — add a document and reindex
POST /api/reindex                — reindex all documents
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.llm_runner import LLMRunner
from app.ollama_runner import OllamaRunner
from app.rag_loader import RAGLoader

settings = get_settings()
llm_runner = None
rag_loader: RAGLoader | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup (directory creation, LLM runner initialisation,
    RAGLoader construction) and shutdown (runner teardown).

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control is handed back to FastAPI while the application
            is running.
    """
    global llm_runner, rag_loader

    # Ensure required directories exist
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.vector_db_dir, exist_ok=True)

    # Select and start the configured LLM backend (optional)
    if settings.enable_llm:
        if settings.llm_backend == "ollama":
            llm_runner = OllamaRunner(
                host=settings.ollama_host,
                port=settings.ollama_port,
                model=settings.ollama_model,
            )
        else:
            # Default: llama_cpp
            llm_runner = LLMRunner(
                model_path=settings.model_path,
                context_size=settings.llama_context_size,
                host=settings.llama_host,
                port=settings.llama_port,
                n_gpu_layers=settings.llama_gpu_layers,
                threads=settings.llama_threads,
                parallel=settings.llama_parallel,
                use_mlock=settings.llama_use_mlock,
                server_bin_path=settings.llama_server_bin,
            )

        started = llm_runner.start_server()
        if not started:
            print(
                f"Warning: {settings.llm_backend} LLM backend failed to start. "
                "LLM queries will be unavailable."
            )
            llm_runner = None

    # Initialise the retrieval pipeline
    rag_loader = RAGLoader(
        data_dir=settings.data_dir,
        storage_dir=settings.vector_db_dir,
        llm_runner=llm_runner,
    )

    yield

    # Teardown — stop the runner if one is active
    if llm_runner is not None:
        llm_runner.stop_server()


app = FastAPI(
    title="Local RAG Workbench",
    description="Local retrieval-augmented generation with optional llama.cpp or Ollama synthesis.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hello")
def hello() -> dict:
    """
    Backend health check.

    Returns:
        dict: Keys:
            - ``status`` (str): Always ``"ok"``.
            - ``message`` (str): Human-readable status line.
            - ``llm_backend`` (str): Active LLM backend name, or
              ``"disabled"`` when ``ENABLE_LLM=false``.
    """
    backend = settings.llm_backend if settings.enable_llm else "disabled"
    return {
        "status": "ok",
        "message": "Local RAG Workbench backend is running.",
        "llm_backend": backend,
    }


@app.get("/api/available-documents")
def available_documents() -> dict:
    """
    List all currently indexed documents.

    Returns:
        dict: ``{ "documents": [ { "source": str, "chunks": int }, ... ] }``
    """
    return {"documents": rag_loader.list_available_documents()}


@app.post("/api/docscan")
async def docscan(request: Request, usellm: bool = False) -> dict:
    """
    Query the RAG system with a user question.

    Retrieves the most relevant document chunks. When ``usellm=true``
    and an LLM backend is configured, synthesises an answer from the
    retrieved context.

    Args:
        request (Request): JSON body with key ``"message"`` (str).
        usellm (bool): Query parameter. ``false`` (default) = retrieval
            only; ``true`` = LLM synthesis.

    Returns:
        dict: ``{ "reply": str }`` — formatted context or LLM answer.
    """
    body = await request.json()
    message = body.get("message", "")
    reply = rag_loader.query(message, use_llm=usellm)
    return {"reply": reply}


@app.post("/api/documents")
async def add_document(request: Request) -> dict:
    """
    Add a new document to the data directory and reindex.

    Args:
        request (Request): JSON body with keys:
            - ``"source"`` (str): Filename for the document (e.g. ``"note.md"``).
            - ``"text"`` (str): Full document text content.

    Returns:
        dict: ``{ "status": "indexed", "source": str, "chunks": int }``
    """
    body = await request.json()
    source = body.get("source", "")
    text = body.get("text", "")
    return rag_loader.add_document(source, text)


@app.post("/api/reindex")
def reindex() -> dict:
    """
    Reindex all documents in the data directory.

    Useful after manually adding, editing, or removing files on disk.

    Returns:
        dict: ``{ "status": "reindexed", "documents": int, "chunks": int }``
    """
    return rag_loader.reindex()
