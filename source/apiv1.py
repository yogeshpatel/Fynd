
from fastapi import APIRouter , Request
from fastapi.params import Depends
from langchain_community.chains.pebblo_retrieval.models import VectorDB

from source.db_manager import DBManager

router = APIRouter()

def get_db_manager(request : Request):
    return request.app.state.db_manager

@router.get("/api/v1/query")
def query(user_query : str, db_manager=Depends(get_db_manager)):
    _manager : DBManager = db_manager
    return _manager.query_document(user_query)