from fastapi import APIRouter
from app.api.v1 import voice, deepseek

api_router = APIRouter(prefix="/api")  # 添加全局前缀

api_router.include_router(
    voice.router, 
    prefix="/v1/voice", 
    tags=["Voice Services"]
)

api_router.include_router(
    deepseek.router, 
    prefix="/v1/deepseek", 
    tags=["AI Chat"]
)
