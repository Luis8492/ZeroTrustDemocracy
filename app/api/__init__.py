from fastapi import APIRouter

from .qa import router as qa_router

api_router = APIRouter()
api_router.include_router(qa_router, prefix="/qa")
