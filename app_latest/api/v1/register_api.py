from fastapi import APIRouter, Depends, HTTPException, status
from models.register.register_schema import UserCreate, UserResponse
from services.register_service import RegisterService
from db.db_digital_manage import DatabaseManager
from core.config import settings

router = APIRouter()

def get_register_service() -> RegisterService:
    """获取注册服务实例"""
    db_manager = DatabaseManager(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        port=settings.DB_PORT,
        charset=settings.DB_CHARSET
    )
    return RegisterService(db_manager)

@router.post("/register", response_model=UserResponse, tags=["Authentication"])
async def register_user(
    user_data: UserCreate,
    register_service: RegisterService = Depends(get_register_service)
):
    try:
        success, user, message = register_service.create_user(user_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        return UserResponse(success=success, message=message, data=user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))