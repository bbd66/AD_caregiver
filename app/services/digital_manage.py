from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional, Dict, Any, List, Union
import time
import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi import UploadFile, File, Form

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger("digital_human_api")

from db import DatabaseManager
from models import (
    DigitalHumanCreate, 
    DigitalHumanResponse, 
    DigitalHumanListResponse,
    DigitalHuman,
    DigitalHumanList
)

app = FastAPI(
    title="数字人管理系统API",
    description="提供数字人数据的添加、删除和查询功能",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该设置为特定域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 临时存储，用于在网络异常时创建本地ID
LOCAL_TEMP_DATA = {}

# 创建静态文件目录
STATIC_DIR = Path("./static")
IMAGES_DIR = STATIC_DIR / "images"
AUDIO_DIR = STATIC_DIR / "audio"
UPLOADS_DIR = STATIC_DIR / "uploads"
AVATARS_DIR = UPLOADS_DIR / "avatars"

# 确保目录存在
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

# 添加静态文件支持
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 依赖项：创建数据库管理器
def get_db():
    db = DatabaseManager()
    try:
        db.connect()
        # 确保表存在
        if not db.check_table_exists():
            db.create_table()
        else:
            # 如果表已存在，检查并添加可能缺失的列
            db.add_missing_columns()
        yield db
    finally:
        db.disconnect()


@app.get("/")
async def root():
    return {"message": "数字人管理系统API"}


@app.post("/digital-humans/", response_model=DigitalHumanResponse)
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
    
    # 确保必要字段存在，如果不存在则设置默认值
    _ensure_required_fields(digital_human_data)
    logger.info(f"添加默认值后的数据: {digital_human_data}")
    
    # avatar字段现在应该是从/upload/image接口获取的URL，无需再处理文件
    # 只需处理音频文件路径
    if 'original_reference_audio_path' in digital_human_data and digital_human_data['original_reference_audio_path']:
        logger.info(f"处理参考音频文件: {digital_human_data['original_reference_audio_path']}")
        reference_audio_url = copy_file_to_static(digital_human_data['original_reference_audio_path'], AUDIO_DIR)
        if reference_audio_url:
            digital_human_data['referenceAudio'] = reference_audio_url
    
    if 'original_training_audio_path' in digital_human_data and digital_human_data['original_training_audio_path']:
        logger.info(f"处理训练音频文件: {digital_human_data['original_training_audio_path']}")
        training_audio_url = copy_file_to_static(digital_human_data['original_training_audio_path'], AUDIO_DIR)
        if training_audio_url:
            digital_human_data['trainingAudio'] = training_audio_url
    
    try:
        # 调用数据库方法添加数字人
        logger.info(f"准备添加到数据库的数据: {digital_human_data}")
        new_id = db.add_digital_human(digital_human_data)
        logger.info(f"数据库返回的ID: {new_id}")
        
        if not new_id:
            logger.warning("数据库未返回ID，创建本地数据")
            # 如果数据库操作失败，创建一个本地临时ID
            local_id = f"local-{int(time.time() * 1000)}"
            digital_human_data['id'] = local_id
            LOCAL_TEMP_DATA[local_id] = digital_human_data
            
            return DigitalHumanResponse(
                success=True,  # 即使是本地创建，也返回成功
                message="创建数字人成功（本地模式）",
                data=DigitalHuman(**digital_human_data)
            )
        
        # 获取创建的数字人数据
        created_human = db.get_digital_human(new_id)
        logger.info(f"从数据库获取的创建结果: {created_human}")
        
        # 确保所有必要字段存在，不存在则设置默认值
        if created_human:
            _ensure_required_fields(created_human)
            logger.info(f"最终返回的数据: {created_human}")
        else:
            logger.error(f"无法从数据库获取刚创建的数字人 ID: {new_id}")
        
        return DigitalHumanResponse(
            success=True,
            message="创建数字人成功",
            data=DigitalHuman(**created_human)
        )
    except Exception as e:
        # 捕获异常，确保即使出错也能返回一个有效的响应
        logger.error(f"创建数字人出错: {e}", exc_info=True)
        
        # 创建一个本地临时ID
        local_id = f"local-{int(time.time() * 1000)}"
        digital_human_data['id'] = local_id
        LOCAL_TEMP_DATA[local_id] = digital_human_data
        
        return DigitalHumanResponse(
            success=True,  # 即使是本地创建，也返回成功
            message="创建数字人成功（本地模式）",
            data=DigitalHuman(**digital_human_data)
        )


@app.get("/digital-humans/", response_model=DigitalHumanListResponse)
async def list_digital_humans(
    skip: int = Query(0, ge=0, description="分页起始位置"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: DatabaseManager = Depends(get_db)
):
    """
    获取数字人列表，支持分页和搜索
    """
    try:
        if search:
            # 使用搜索功能
            humans, total = db.search_digital_humans(search, skip, limit)
        else:
            # 使用分页功能
            humans, total = db.get_digital_humans_with_pagination(skip, limit)
        
        logger.info(f"从数据库获取的数据: {humans}")
        
        # 确保每条记录都有必要的字段
        for human in humans:
            _ensure_required_fields(human)
        
        logger.info(f"添加默认值后的数据: {humans}")
        
        # 添加临时创建的本地数据（如果有）
        local_humans = list(LOCAL_TEMP_DATA.values())
        if local_humans and not search:  # 在搜索模式下不添加本地数据
            total += len(local_humans)
            if skip < len(local_humans):
                # 只添加在当前分页范围内的本地数据
                local_to_add = local_humans[skip:skip+limit]
                humans = local_to_add + humans
                if len(humans) > limit:
                    humans = humans[:limit]
        
        return DigitalHumanListResponse(
            success=True,
            message="获取数字人列表成功",
            data=DigitalHumanList(
                items=[DigitalHuman(**human) for human in humans],
                total=total
            )
        )
    except Exception as e:
        logger.error(f"获取数字人列表出错: {e}", exc_info=True)
        # 返回本地数据作为备份
        local_humans = list(LOCAL_TEMP_DATA.values())
        
        return DigitalHumanListResponse(
            success=True,
            message="获取数字人列表成功（本地模式）",
            data=DigitalHumanList(
                items=[DigitalHuman(**human) for human in local_humans],
                total=len(local_humans)
            )
        )


@app.get("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def get_digital_human(
    digital_human_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    获取指定ID的数字人
    """
    logger.info(f"获取数字人 ID: {digital_human_id}")
    
    # 检查是否是本地临时ID
    if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
        local_data = LOCAL_TEMP_DATA[digital_human_id]
        _ensure_required_fields(local_data)
        logger.info(f"从本地存储获取的数据: {local_data}")
        
        return DigitalHumanResponse(
            success=True,
            message="获取数字人成功（本地模式）",
            data=DigitalHuman(**local_data)
        )
    
    try:
        # 尝试从数据库获取
        human = db.get_digital_human(int(digital_human_id))
        logger.info(f"从数据库获取的数据: {human}")
        
        if not human:
            logger.warning(f"数据库中不存在ID为{digital_human_id}的数字人")
            return DigitalHumanResponse(
                success=False,
                message=f"ID为{digital_human_id}的数字人不存在"
            )
        
        # 确保所有必要字段存在
        _ensure_required_fields(human)
        logger.info(f"添加默认值后的数据: {human}")
        
        return DigitalHumanResponse(
            success=True,
            message="获取数字人成功",
            data=DigitalHuman(**human)
        )
    except ValueError:
        # 如果ID不是整数也不是有效的本地ID
        logger.error(f"无效的ID格式: {digital_human_id}")
        return DigitalHumanResponse(
            success=False,
            message=f"无效的ID格式: {digital_human_id}"
        )
    except Exception as e:
        logger.error(f"获取数字人信息出错: {e}", exc_info=True)
        return DigitalHumanResponse(
            success=False,
            message=f"获取数字人信息时发生错误"
        )


@app.delete("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def delete_digital_human(
    digital_human_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    删除指定ID的数字人
    """
    logger.info(f"删除数字人 ID: {digital_human_id}")
    
    # 检查是否是本地临时ID
    if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
        # 从本地存储中删除
        del LOCAL_TEMP_DATA[digital_human_id]
        logger.info(f"从本地存储删除ID为{digital_human_id}的数字人")
        
        return DigitalHumanResponse(
            success=True,
            message=f"成功删除ID为{digital_human_id}的数字人（本地模式）"
        )
    
    try:
        # 尝试从数据库删除
        # 先检查数字人是否存在
        existing_human = db.get_digital_human(int(digital_human_id))
        if not existing_human:
            logger.warning(f"数据库中不存在ID为{digital_human_id}的数字人")
            return DigitalHumanResponse(
                success=False,
                message=f"ID为{digital_human_id}的数字人不存在"
            )
        
        # 删除数字人
        success = db.delete_digital_human(int(digital_human_id))
        logger.info(f"删除结果: {success}")
        
        if not success:
            logger.error(f"删除ID为{digital_human_id}的数字人失败")
            return DigitalHumanResponse(
                success=False,
                message="删除数字人失败"
            )
        
        return DigitalHumanResponse(
            success=True,
            message=f"成功删除ID为{digital_human_id}的数字人"
        )
    except ValueError:
        # 如果ID不是整数也不是有效的本地ID
        logger.error(f"无效的ID格式: {digital_human_id}")
        return DigitalHumanResponse(
            success=False,
            message=f"无效的ID格式: {digital_human_id}"
        )
    except Exception as e:
        logger.error(f"删除数字人出错: {e}", exc_info=True)
        return DigitalHumanResponse(
            success=False,
            message=f"删除数字人时发生错误"
        )


@app.post("/upload/image")
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


@app.post("/upload/reference-audio")
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


@app.post("/upload/training-audio")
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


@app.put("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def update_digital_human(
    digital_human_id: str,
    request: Request,
    db: DatabaseManager = Depends(get_db)
):
    """
    更新指定ID的数字人信息
    """
    logger.info(f"更新数字人 ID: {digital_human_id}")
    
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
    
    # 检查是否是本地临时ID
    if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
        # 更新本地数据
        for key, value in update_data.items():
            LOCAL_TEMP_DATA[digital_human_id][key] = value
        
        # avatar和音频URL应该已经在前端通过上传接口获取
        # 仅备份，以防有旧的处理方式，通常不会执行
        if 'original_reference_audio_path' in update_data and update_data['original_reference_audio_path']:
            reference_audio_url = copy_file_to_static(update_data['original_reference_audio_path'], AUDIO_DIR)
            if reference_audio_url:
                LOCAL_TEMP_DATA[digital_human_id]['referenceAudio'] = reference_audio_url
        
        if 'original_training_audio_path' in update_data and update_data['original_training_audio_path']:
            training_audio_url = copy_file_to_static(update_data['original_training_audio_path'], AUDIO_DIR)
            if training_audio_url:
                LOCAL_TEMP_DATA[digital_human_id]['trainingAudio'] = training_audio_url
        
        updated_data = LOCAL_TEMP_DATA[digital_human_id]
        
        logger.info(f"本地更新后的数据: {updated_data}")
        _ensure_required_fields(updated_data)
        
        return DigitalHumanResponse(
            success=True,
            message="更新数字人成功（本地模式）",
            data=DigitalHuman(**updated_data)
        )
    
    try:
        # 检查数字人是否存在
        existing_human = db.get_digital_human(int(digital_human_id))
        if not existing_human:
            logger.warning(f"数据库中不存在ID为{digital_human_id}的数字人")
            return DigitalHumanResponse(
                success=False,
                message=f"ID为{digital_human_id}的数字人不存在"
            )
        
        # avatar和音频URL应该已经在前端通过上传接口获取
        # 仅备份，以防有旧的处理方式，通常不会执行
        if 'original_reference_audio_path' in update_data and update_data['original_reference_audio_path']:
            reference_audio_url = copy_file_to_static(update_data['original_reference_audio_path'], AUDIO_DIR)
            if reference_audio_url:
                update_data['referenceAudio'] = reference_audio_url
        
        if 'original_training_audio_path' in update_data and update_data['original_training_audio_path']:
            training_audio_url = copy_file_to_static(update_data['original_training_audio_path'], AUDIO_DIR)
            if training_audio_url:
                update_data['trainingAudio'] = training_audio_url
        
        # 调用数据库更新方法
        success = db.update_digital_human(int(digital_human_id), update_data)
        if not success:
            logger.error(f"更新ID为{digital_human_id}的数字人失败")
            return DigitalHumanResponse(
                success=False,
                message="更新数字人失败"
            )
        
        # 获取更新后的数据
        updated_human = db.get_digital_human(int(digital_human_id))
        if not updated_human:
            logger.error(f"无法获取更新后的数字人信息")
            return DigitalHumanResponse(
                success=False,
                message="获取更新后的数字人信息失败"
            )
        
        # 确保所有必要字段存在
        _ensure_required_fields(updated_human)
        logger.info(f"更新后的数据: {updated_human}")
        
        return DigitalHumanResponse(
            success=True,
            message="更新数字人成功",
            data=DigitalHuman(**updated_human)
        )
    except ValueError:
        # 如果ID不是整数也不是有效的本地ID
        logger.error(f"无效的ID格式: {digital_human_id}")
        return DigitalHumanResponse(
            success=False,
            message=f"无效的ID格式: {digital_human_id}"
        )
    except Exception as e:
        logger.error(f"更新数字人信息出错: {e}", exc_info=True)
        return DigitalHumanResponse(
            success=False,
            message=f"更新数字人信息时发生错误"
        )


# 启动应用
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
