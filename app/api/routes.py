from fastapi import APIRouter
from app.api.v1 import voice, deepseek # 新增deepseek导入
from app.api.v1 import voice, avatar_builder

api_router = APIRouter()
api_router.include_router(voice.router, prefix="/v1/voice", tags=["voice"])
api_router.include_router(avatar_builder.router, prefix="/v1/avatar-builder", tags=["avatar-builder"]) 
api_router.include_router(deepseek.router, prefix="/v1/deepseek", tags=["deepseek"])
