from fastapi import APIRouter
from pydantic import BaseModel
import json
from scripts.neo4j_QA import run_query

router = APIRouter(prefix="/api/chat")

class ChatRequest(BaseModel):
    message: str
    openAiKey: str

@router.post("/")
def chat(req: ChatRequest):
    # Starts the question-answering process and returns the result
    result = run_query(req.message, req.openAiKey)
    return {"result": json.loads(result)}