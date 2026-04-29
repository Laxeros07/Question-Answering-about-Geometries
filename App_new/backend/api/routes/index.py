# backend/api/routes/index.py
from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/")
def root():
    return {"message": "API läuft"}