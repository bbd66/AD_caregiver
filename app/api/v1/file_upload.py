from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import os
import uuid
import time
from pathlib import Path
import logging
from typing import Dict, Any

# 创建路由器
router = APIRouter()

# 设置日志
logger = logging.getLogger(__name__)

# 设置上传目录
AVATARS_DIR = Path("static/uploads/avatars")
AUDIO_DIR = Path("static/audio")

# 确保目录存在
AVATARS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 文件上传
# 功能：上传数字人头像
# 文件类型：JPG/PNG
# 返回：图片访问URL
@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    处理图片上传
    """
    logger.info(f"接收到图片上传: {file.filename}")
    
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    content_type = file.content_type
    
    if content_type not in allowed_types:
        logger.warning(f"不支持的文件类型: {content_type}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "上传失败：文件格式不支持，仅支持JPG、PNG格式"
            }
        )
    
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}_{int(time.time())}{file_extension}"
        file_path = AVATARS_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 生成访问URL
        image_url = f"/static/uploads/avatars/{unique_filename}"
        logger.info(f"图片已保存: {file_path}, URL: {image_url}")
        
        return {
            "success": True,
            "imageUrl": image_url,
            "message": "上传成功"
        }
    except Exception as e:
        logger.error(f"图片上传出错: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"上传失败：服务器处理错误 - {str(e)}"
            }
        )



# 功能：上传参考音频
# 文件类型：WAV/MP3
# 返回：音频访问URL
@router.post("/upload/reference-audio")
async def upload_reference_audio(file: UploadFile = File(...)):
    """
    处理参考音频上传
    """
    logger.info(f"接收到参考音频上传: {file.filename}")
    
    # 检查文件类型
    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav"]
    content_type = file.content_type
    
    if content_type not in allowed_types:
        logger.warning(f"不支持的文件类型: {content_type}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "上传失败：文件格式不支持，仅支持WAV、MP3格式"
            }
        )
    
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"ref_{uuid.uuid4()}_{int(time.time())}{file_extension}"
        file_path = AUDIO_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 生成访问URL
        audio_url = f"/static/audio/{unique_filename}"
        logger.info(f"参考音频已保存: {file_path}, URL: {audio_url}")
        
        return {
            "success": True,
            "audioUrl": audio_url,
            "message": "上传成功"
        }
    except Exception as e:
        logger.error(f"参考音频上传出错: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"上传失败：服务器处理错误 - {str(e)}"
            }
        )



# 功能：上传训练音频
# 文件类型：WAV/MP3
# 返回：音频访问URL
@router.post("/upload/training-audio")
async def upload_training_audio(file: UploadFile = File(...)):
    """
    处理训练音频上传
    """
    logger.info(f"接收到训练音频上传: {file.filename}")
    
    # 检查文件类型
    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav"]
    content_type = file.content_type
    
    if content_type not in allowed_types:
        logger.warning(f"不支持的文件类型: {content_type}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "上传失败：文件格式不支持，仅支持WAV、MP3格式"
            }
        )
    
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"train_{uuid.uuid4()}_{int(time.time())}{file_extension}"
        file_path = AUDIO_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 生成访问URL
        audio_url = f"/static/audio/{unique_filename}"
        logger.info(f"训练音频已保存: {file_path}, URL: {audio_url}")
        
        return {
            "success": True,
            "audioUrl": audio_url,
            "message": "上传成功"
        }
    except Exception as e:
        logger.error(f"训练音频上传出错: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"上传失败：服务器处理错误 - {str(e)}"
            }
        )


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

