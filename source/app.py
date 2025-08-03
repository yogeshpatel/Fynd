from contextlib import asynccontextmanager

from fastapi import FastAPI
from apiv1 import router
from db_manager import DBManager

# create Fast api root with show default server status running
# User prot 9100 to run in local host
# Crate addition api end point for api/v1
data_path = "/media/Yogesh/DATA_2TB_M2/llm_db/rag_raw_data"
db_path = "/media/Yogesh/DATA_2TB_M2/llm_db/vector_db"


# Your main application logic here
print("RAG-based application started.")
# Create method to run code once application or method is first crated not every time

db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager = DBManager(data_path, db_path, 1000, 200)
    db_manager.load_documents()
    db_manager.save_document()
    app.state.db_manager = db_manager
    print("db manager loaded")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "running"}

app.include_router(router, dependencies=db_manager)

print("EOL")