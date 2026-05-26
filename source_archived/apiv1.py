"""
[ARCHIVED] API v1 router — legacy prototype v0.

Exposed a single query endpoint backed by DBManager.

Status
------
Superseded by the five endpoints in ``backend/app/main.py``.

This file is kept for historical reference only. Do not run it.
"""

from fastapi import APIRouter, Depends, Request

from source_archived.db_manager import DBManager

router = APIRouter()


def get_db_manager(request: Request) -> DBManager:
    """
    FastAPI dependency that retrieves the shared DBManager instance.

    Reads the manager from ``app.state``, which is set during application
    startup in the lifespan context defined in ``app.py``.

    Args:
        request (Request): The incoming HTTP request (injected by FastAPI).

    Returns:
        DBManager: The shared DBManager instance for this application.
    """
    return request.app.state.db_manager


@router.get("/api/v1/query")
def query(user_query: str, db_manager: DBManager = Depends(get_db_manager)) -> dict:
    """
    Query the FAISS vector store and return a synthesised answer.

    Args:
        user_query (str): The user's question passed as a query parameter.
        db_manager (DBManager): Injected via :func:`get_db_manager`.

    Returns:
        dict: LangChain retrieval chain response containing the answer
            and source documents.
    """
    return db_manager.query_document(user_query)
