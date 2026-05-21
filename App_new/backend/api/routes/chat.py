from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from scripts.neo4j_QA import run_query
from scripts.agent_script import run_question

router = APIRouter(prefix="/api/chat")


class ChatRequest(BaseModel):
    message: str
    openAiKey: str
    selectedModel: str


@router.post("/")
def chat(req: ChatRequest):
    # Starts the question-answering process and returns the result
    try:
        #result = run_query(req.message, req.openAiKey)
        #return {"result": json.loads(result)}
        result = run_question(req.message, req.openAiKey, req.selectedModel)
        return {"result": result}
    except Exception as e:
        # Return a clean JSON error so CORS middleware can add headers
        return JSONResponse(status_code=500, content={"error": "internal server error", "details": str(e)})
    