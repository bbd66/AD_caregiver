# 虚拟形象的实现逻辑 反应逻辑

# 虚拟形象构建服务
import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import BackgroundTasks
from uuid import uuid4
from PIL import Image
import io

from app.db.session import get_db
from app.models.avatar_builder import Avatar
from app.services.file_storage import FileStorageService
from app.core.config import settings
from app.core.logging import logger

class AvatarBuilderService:
    def __init__(self):
        self.file_storage = FileStorageService()
    
    async def create_avatar(
        self,
        user_id: int,
        name: str,
        image_data: bytes,
        image_path: str,
        description: Optional[str] = None,
        style: Optional[str] = None,
        tags: List[str] = [],
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Avatar:
        """创建新的虚拟形象"""
        # 1. 保存原始图像
        original_path = await self.file_storage.save_file(image_data, image_path)
        
        # 2. 生成缩略图
        thumbnail_data = await self._generate_thumbnail(image_data)
        thumbnail_path = image_path.replace(".", "_thumbnail.")
        thumbnail_path = await self.file_storage.save_file(thumbnail_data, thumbnail_path)
        
        # 3. 创建数据库记录
        db = await get_db()
        avatar_id = await self._get_next_id(db, "avatars")
        
        now = datetime.utcnow()
        avatar_data = {
            "_id": avatar_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "original_image_path": original_path,
            "thumbnail_path": thumbnail_path,
            "style": style,
            "tags": tags,
            "generated_variants": [],
            "created_at": now,
            "updated_at": now
        }
        
        await db.avatars.insert_one(avatar_data)
        
        # 4. 更新用户的头像计数
        await db.users.update_one(
            {"_id": user_id},
            {"$inc": {"avatar_count": 1}}
        )
        
        # 5. 在后台执行初始处理（如果需要）
        if background_tasks:
            background_tasks.add_task(
                self._process_avatar_background,
                avatar_id,
                user_id,
                image_data
            )
        
        # 6. 返回模型对象
        return Avatar(
            id=avatar_id,
            user_id=user_id,
            name=name,
            description=description,
            original_image_path=original_path,
            thumbnail_path=thumbnail_path,
            style=style,
            tags=tags,
            generated_variants=[],
            created_at=now,
            updated_at=now
        )
    
    async def _generate_thumbnail(self, image_data: bytes, max_size: int = 256) -> bytes:
        """生成缩略图"""
        try:
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((max_size, max_size))
            
            # 保存为JPEG格式
            output = io.BytesIO()
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            # 如果失败，返回原始图像
            return image_data
    
    async def _get_next_id(self, db, collection_name: str) -> int:
        """获取自增ID"""
        counter = await db.counters.find_one_and_update(
            {"_id": collection_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return counter["seq"]
    
    async def _process_avatar_background(self, avatar_id: int, user_id: int, image_data: bytes):
        """后台处理新上传的头像"""
        try:
            # 这里可以进行一些耗时处理，例如:
            # 1. 图像优化
            # 2. 背景移除
            # 3. 特征检测
            # 4. 推荐风格生成
            
            # 模拟处理时间
            time.sleep(2)
            
            # 更新处理状态
            db = await get_db()
            await db.avatars.update_one(
                {"_id": avatar_id},
                {"$set": {"processing_complete": True}}
            )
            
            logger.info(f"Background processing completed for avatar {avatar_id}")
        except Exception as e:
            logger.error(f"Error in background processing for avatar {avatar_id}: {str(e)}")


# 虚拟形象删除服务
class AvatarBuilderService:
    # 其他方法...
    
    async def get_avatar(self, avatar_id: int, user_id: int) -> Optional[models.Avatar]:
        """获取虚拟形象，并验证所有权"""
        db = await get_db()
        avatar = await db.avatars.find_one({"_id": avatar_id})
        
        # 验证所有权
        if not avatar or avatar["user_id"] != user_id:
            return None
            
        return models.Avatar(**avatar)
    
    async def delete_avatar(self, avatar_id: int) -> bool:
        """删除虚拟形象及相关资源"""
        db = await get_db()
        
        # 查找虚拟形象以获取文件信息
        avatar = await db.avatars.find_one({"_id": avatar_id})
        if not avatar:
            return False
            
        # 1. 删除相关文件
        file_paths = [
            avatar["original_image_path"],
            avatar["thumbnail_path"],
            *avatar.get("generated_variants", [])
        ]
        
        for file_path in file_paths:
            if file_path:
                try:
                    await self.file_storage.delete_file(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {str(e)}")
        
        # 2. 删除数据库记录
        result = await db.avatars.delete_one({"_id": avatar_id})
        
        # 3. 删除相关生成任务记录
        await db.generation_tasks.delete_many({"avatar_id": avatar_id})
        
        # 4. 更新用户的头像统计
        await db.users.update_one(
            {"_id": avatar["user_id"]},
            {"$inc": {"avatar_count": -1}}
        )
        
        return result.deleted_count > 0

  #
