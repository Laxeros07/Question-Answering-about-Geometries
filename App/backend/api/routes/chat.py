from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import traceback
from scripts.agent_script import run_question

router = APIRouter(prefix="/api/chat")


class ChatRequest(BaseModel):
    message: str
    openAiKey: str
    selectedModel: str


@router.post("")
def chat(req: ChatRequest):
    # Starts the question-answering process and returns the result
    try:
        print(f"Request: model={req.selectedModel}, question={req.message}")

        result = run_question(req.message, req.openAiKey, req.selectedModel)
        return {"result": result}

    except Exception as e:
        # Print the full traceback to the terminal
        tb = traceback.format_exc()
        print("=" * 70)
        print(f"ERROR in /api/chat: {type(e).__name__}")
        print(tb)
        print("=" * 70)

        # Return a clean JSON error so CORS middleware can add headers
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal server error",
                "details": str(e),
                "error_type": type(e).__name__,
                "trace": tb,
            },
        )
