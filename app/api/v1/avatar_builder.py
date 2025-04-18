from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional

from app.services.avatar_builder import AvatarBuilderService

router = APIRouter()
service = AvatarBuilderService()

# 虚拟形象构建路由
@router.post("/avatars/", response_model=schemas.Avatar)
async def create_avatar(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: UploadFile = File(...),
    background_tasks: BackgroundTasks
):
    """创建新的虚拟形象"""
    return await service.create_avatar(name, description, image, background_tasks)

# 虚拟形象获取路由
@router.get("/avatars/{avatar_id}", response_model=schemas.AvatarDetail)
async def get_avatar(
    avatar_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """获取虚拟形象详情"""
    avatar = await service.get_avatar(avatar_id=avatar_id, user_id=user_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

# 虚拟形象更新路由
@router.put("/avatars/{avatar_id}", response_model=schemas.Avatar)
async def update_avatar(
    avatar_id: int,
    update_data: schemas.AvatarUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """更新虚拟形象信息"""
    avatar = await service.get_avatar(avatar_id=avatar_id, user_id=user_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    return await service.update_avatar(avatar_id=avatar_id, update_data=update_data)

# 虚拟形象删除路由
@router.delete("/avatars/{avatar_id}", status_code=204)
async def delete_avatar(
    avatar_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """删除虚拟形象"""
    avatar = await service.get_avatar(avatar_id=avatar_id, user_id=user_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    await service.delete_avatar(avatar_id=avatar_id)
    return None  # 204状态码表示成功但无内容返回

#   示例：@router.post("/build", response_model=AvatarBuildResponse)
