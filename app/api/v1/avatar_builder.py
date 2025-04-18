from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional

from app.services.avatar_builder import AvatarBuilderService

router = APIRouter()
service = AvatarBuilderService()

#   示例：@router.post("/build", response_model=AvatarBuildResponse)
