"""
[ARCHIVED] FastAPI application entry point — legacy prototype v0.

Wired DBManager to a FastAPI app using a lifespan context. Paths were
hardcoded to a specific local drive.

Status
------
Superseded by ``backend/app/main.py``, which loads all paths from
environment variables and supports multiple LLM backends.

This file is kept for historical reference only. Do not run it.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from source_archived.apiv1 import router
from source_archived.db_manager import DBManager

# NOTE: These paths were hardcoded to the original development machine.
# The new backend resolves paths via environment variables in backend/.env.
DATA_PATH = "/media/Yogesh/DATA_2TB_M2/llm_db/rag_raw_data"
DB_PATH = "/media/Yogesh/DATA_2TB_M2/llm_db/vector_db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context — initialises DBManager on startup.

    Loads and saves documents, then attaches the manager instance to
    ``app.state`` so route handlers can access it via dependency injection.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control is handed back to FastAPI while the application runs.
    """
    db_manager = DBManager(DATA_PATH, DB_PATH, chunk_size=1000, chunk_overlap=200)
    db_manager.load_documents()
    db_manager.save_document()
    app.state.db_manager = db_manager
    print("DBManager loaded.")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root() -> dict:
    """
    Root health-check endpoint.

    Returns:
        dict: ``{ "status": "running" }``
    """
    return {"status": "running"}


app.include_router(router)
