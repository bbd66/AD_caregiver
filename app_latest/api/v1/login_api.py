from fastapi import APIRouter, Depends, HTTPException, status
from models.login.login_schema import LoginRequest, LoginResponse
from services.login_service import LoginService
from db.db_digital_manage import DatabaseManager
from core.config import settings

router = APIRouter()

def get_login_service() -> LoginService:
    """获取登录服务实例"""
    db_manager = DatabaseManager(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        port=settings.DB_PORT,
        charset=settings.DB_CHARSET
    )
    return LoginService(db_manager)

@router.post("/login", response_model=LoginResponse, tags=["Authentication"])
async def login_user(
    login_request: LoginRequest,
    login_service: LoginService = Depends(get_login_service)
):
    success, user, message = login_service.authenticate_user(login_request.username, login_request.password)
    if not success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
    return LoginResponse(success=success, message=message, data=user)