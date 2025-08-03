
from fastapi import APIRouter , Request
from fastapi.params import Depends

router = APIRouter()

def get_db_manager(request : Request):
    return request.app.state.db_manager

@router.get("/api/v1/add")
def add(a: int, b: int, db_manager=Depends(get_db_manager)):
    return {"result": a + b}