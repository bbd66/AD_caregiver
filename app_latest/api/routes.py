from fastapi import APIRouter
from api.v1 import voice, deepseek, digital_manage, file_upload, register_api, login_api,document  # 导入新的路由

api_router = APIRouter()  # Global router

# API version 1 router
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(
    voice.router, 
    prefix="/voice", 
    tags=["Voice Services"]
)

v1_router.include_router(
    deepseek.router, 
    prefix="/deepseek", 
    tags=["AI Chat"]
)

v1_router.include_router(
    digital_manage.router, 
    prefix="/digital", 
    tags=["Digital Human Management"]
)

v1_router.include_router(
    file_upload.router, 
    prefix="/files", 
    tags=["File Upload"]
)

v1_router.include_router(
    document.router, 
    prefix="/documents", 
    tags=["Documents File"]
)

# 包含新的注册和登录路由
v1_router.include_router(
    register_api.router, 
    prefix="/auth", 
    tags=["Authentication"]
)

v1_router.include_router(
    login_api.router, 
    prefix="/auth", 
    tags=["Authentication"]
)

# Include v1 router in the main API router
api_router.include_router(v1_router, prefix="/api")