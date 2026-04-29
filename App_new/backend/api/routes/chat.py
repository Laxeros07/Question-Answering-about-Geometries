from fastapi import APIRouter
from pydantic import BaseModel
from scripts.neo4j_QA import run_query

router = APIRouter(prefix="/api/chat")

class ChatRequest(BaseModel):
    message: str
    openAiKey: str

@router.post("/")
def chat(req: ChatRequest):
    result = run_query(req.message, req.openAiKey)
    return {"result": result}