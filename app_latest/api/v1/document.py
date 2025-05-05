from fastapi import APIRouter, HTTPException
from typing import List
from db import app_db
from schemas.document import DocumentRequest, DocumentResponse
router = APIRouter()

@router.get("/user/{user_id}", response_model=List[DocumentResponse])
async def get_user_documents(user_id: int):  # 直接接收路径参数
    """
    获取指定用户的所有文档
    
    - user_id: 用户唯一标识ID
    """
    db_manager = app_db.DatabaseManager()
    print(f"正在查询用户 {user_id} 的文档...")
    try:
        documents = db_manager.get_documents_by_user_id(user_id)
        if not documents:
            return []
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取文档失败: {str(e)}"
        )