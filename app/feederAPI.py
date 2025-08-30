from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import qa_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],  # フロントエンドのポートを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(qa_router)
