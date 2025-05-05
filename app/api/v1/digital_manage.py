from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse
import json
import time
import logging
import os
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

# 导入数据库和模型
from db.db_digital_manage import DatabaseManager, get_db
from models.digital_manage import DigitalHuman, DigitalHumanCreate, DigitalHumanResponse, DigitalHumanList, DigitalHumanListResponse
from services.digital_manage import digital_manage_service

# 创建路由器
router = APIRouter()

# 日志设置
logger = logging.getLogger(__name__)

# 路径设置
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 临时存储
LOCAL_TEMP_DATA = {}

# 根路由 
# 功能：API健康检查端点
@router.get("/")
async def root():
    return {"message": "数字人管理系统API"}

# 数字人管理 
# 功能：创建新数字人
# 参数：DigitalHumanCreate模型（JSON Body）
#      包含音频文件路径字段
# 响应：DigitalHumanResponse（含创建结果）
@router.post("/digital-humans/", response_model=DigitalHumanResponse)
async def create_digital_human(
    request: Request,
    digital_human: DigitalHumanCreate,
    db: DatabaseManager = Depends(get_db)
):
    """
    创建新的数字人
    """
    # 记录原始请求体，以检查路径字段
    body = await request.body()
    try:
        raw_data = json.loads(body)
        logger.info(f"收到原始请求数据: {raw_data}")
    except:
        logger.info(f"无法解析原始请求数据: {body}")
        
    digital_human_data = digital_human.model_dump(exclude_unset=True)
    logger.info(f"Pydantic模型解析后的数据: {digital_human_data}")
    
    # 调用服务层进行处理
    success, data, message = digital_manage_service.create_digital_human(digital_human_data, db)
    
    return DigitalHumanResponse(
        success=success,
        message=message,
        data=DigitalHuman(**data) if data else None
    )

# 功能：获取数字人列表（支持分页/搜索）
# 路径参数：user_id: 用户ID
# 查询参数：skip: 分页起始位置
#          limit: 每页数量（1-100）
#          search: 搜索关键词
# 响应：DigitalHumanListResponse（含分页结果）
@router.get("/digital-humans/{user_id}", response_model=DigitalHumanListResponse)
async def list_digital_humans(
    user_id: int,
    skip: int = Query(0, ge=0, description="分页起始位置"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: DatabaseManager = Depends(get_db)
):
    """
    获取指定用户的数字人列表，支持分页和搜索
    """
    humans, total = digital_manage_service.get_digital_humans(skip, limit, search, user_id, db)
    
    return DigitalHumanListResponse(
        success=True,
        message="获取数字人列表成功",
        data=DigitalHumanList(
            items=[DigitalHuman(**human) for human in humans],
            total=total
        )
    )

# 功能：获取单个数字人详情
# 路径参数：
# user_id: 用户ID
# digital_human_id: 数字人ID（支持local-前缀的临时ID）
# 响应：DigitalHumanResponse
@router.get("/digital-humans/{user_id}/{digital_human_id}", response_model=DigitalHumanResponse)
async def get_digital_human(
    user_id: int,
    digital_human_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    获取指定用户的指定ID的数字人
    """
    success, data, message = digital_manage_service.get_digital_human(digital_human_id, user_id, db)
    
    return DigitalHumanResponse(
        success=success,
        message=message,
        data=DigitalHuman(**data) if data else None
    )

# 功能：删除数字人
# 路径参数：
# digital_human_id: 数字人ID（支持临时ID）
# 响应：操作结果
@router.delete("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def delete_digital_human(
    digital_human_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    删除指定ID的数字人
    """
    success, message = digital_manage_service.delete_digital_human(digital_human_id, db)
    
    return DigitalHumanResponse(
        success=success,
        message=message
    )

# 功能：更新数字人信息
# 参数：
# 路径参数：digital_human_id
# JSON Body更新字段
# 响应：更新后的完整数据
@router.put("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def update_digital_human(
    digital_human_id: str,
    request: Request,
    db: DatabaseManager = Depends(get_db)
):
    """
    更新指定ID的数字人信息
    """
    # 获取请求体数据
    body = await request.body()
    try:
        update_data = json.loads(body)
        logger.info(f"收到更新请求数据: {update_data}")
    except Exception as e:
        logger.error(f"解析请求数据失败: {e}", exc_info=True)
        return DigitalHumanResponse(
            success=False,
            message="请求数据格式无效"
        )
    
    # 调用服务层
    success, data, message = digital_manage_service.update_digital_human(digital_human_id, update_data, db)
    
    return DigitalHumanResponse(
        success=success,
        message=message,
        data=DigitalHuman(**data) if data else None
    )

# 辅助函数
def copy_file_to_static(file_path, target_dir):
    """复制文件到静态目录，返回访问URL"""
    try:
        if not os.path.exists(file_path):
            logger.error(f"源文件不存在: {file_path}")
            return None
        
        # 生成唯一文件名
        file_name = os.path.basename(file_path)
        unique_filename = f"{int(time.time())}_{file_name}"
        target_path = os.path.join(target_dir, unique_filename)
        
        # 复制文件
        shutil.copy2(file_path, target_path)
        
        # 返回URL路径
        if str(target_dir).endswith("audio"):
            return f"/static/audio/{unique_filename}"
        else:
            return f"/static/{unique_filename}"
    except Exception as e:
        logger.error(f"复制文件失败: {e}", exc_info=True)
        return None

def _ensure_required_fields(data: Dict[str, Any]):
    """确保数据中包含所有必要的字段，不存在则设置默认值"""
    if 'id' not in data:
        data['id'] = f"local-{int(time.time() * 1000)}"
        
    if 'description' not in data or not data['description']:
        data['description'] = f"{data.get('name', '未命名')} 的描述"
        
    if 'referenceAudio' not in data or not data['referenceAudio']:
        data['referenceAudio'] = ''
        
    if 'trainingAudio' not in data or not data['trainingAudio']:
        data['trainingAudio'] = ''
        
    if 'avatar' not in data or not data['avatar']:
        data['avatar'] = ''
        
    if 'phone' not in data or not data['phone']:
        data['phone'] = ''
