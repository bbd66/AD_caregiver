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

# 虚拟形象获取服务
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import re

from app.db.session import get_db
from app.models.avatar_builder import Avatar
from app.core.logging import logger

class AvatarBuilderService:
    # ... (其他方法保持不变)
    
    async def get_avatars(
        self,
        filters: Dict[str, Any],
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Avatar]:
        """获取虚拟形象列表"""
        db = await get_db()
        
        # 构建查询条件
        query = filters.copy()
        
        # 添加搜索条件（如果提供）
        if search_query:
            # 使用正则表达式进行不区分大小写的搜索
            search_regex = {"$regex": search_query, "$options": "i"}
            query["$or"] = [
                {"name": search_regex},
                {"description": search_regex},
                {"tags": search_query}  # 精确匹配标签
            ]
        
        # 准备排序
        sort_direction = -1 if sort_order == "desc" else 1
        sort_options = {sort_by: sort_direction}
        
        # 执行查询
        cursor = db.avatars.find(query).sort(sort_options).skip(skip).limit(limit)
        
        # 将结果转换为模型
        avatars = []
        async for doc in cursor:
            avatars.append(Avatar(**doc))
        
        return avatars
    
    async def get_avatar(self, avatar_id: int, user_id: int) -> Optional[Avatar]:
        """获取单个虚拟形象"""
        db = await get_db()
        
        # 获取记录并验证所有权
        doc = await db.avatars.find_one({"_id": avatar_id})
        
        # 检查是否存在及所有权
        if not doc or doc["user_id"] != user_id:
            return None
        
        # 转换为模型对象
        return Avatar(**doc)
    
    async def update_last_accessed(self, avatar_id: int):
        """更新虚拟形象的最后访问时间"""
        db = await get_db()
        
        await db.avatars.update_one(
            {"_id": avatar_id},
            {"$set": {"last_accessed": datetime.utcnow()}}
        )
    
    async def get_avatar_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户的虚拟形象统计信息"""
        db = await get_db()
        
        # 获取总数
        total_count = await db.avatars.count_documents({"user_id": user_id})
        
        # 按风格分组统计
        style_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$style", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        style_cursor = db.avatars.aggregate(style_pipeline)
        styles = {}
        async for doc in style_cursor:
            style_name = doc["_id"] or "unspecified"
            styles[style_name] = doc["count"]
        
        # 获取最近创建的
        recent_cursor = db.avatars.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(5)
        
        recent = []
        async for doc in recent_cursor:
            recent.append({
                "id": doc["_id"],
                "name": doc["name"],
                "thumbnail_path": doc["thumbnail_path"],
                "created_at": doc["created_at"]
            })
        
        # 返回统计结果
        return {
            "total": total_count,
            "by_style": styles,
            "recent": recent
        }

# 虚拟形象更新服务
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import os
from PIL import Image
import io

from app.db.session import get_db
from app.models.avatar_builder import Avatar
from app.services.file_storage import FileStorageService
from app.core.cache import avatar_cache
from app.core.logging import logger
from app.core.config import settings

class AvatarBuilderService:
    def __init__(self):
        self.file_storage = FileStorageService()
    
    # ... (其他方法保持不变)
    
    async def update_avatar(
        self,
        avatar_id: int,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Avatar:
        """
        更新虚拟形象的基本信息
        
        :param avatar_id: 虚拟形象ID
        :param user_id: 用户ID，用于权限验证
        :param update_data: 要更新的字段和值
        :return: 更新后的虚拟形象
        """
        db = await get_db()
        
        # 确保更新数据不包含不可修改的字段
        safe_update = {k: v for k, v in update_data.items() if k in [
            "name", "description", "style", "tags"
        ]}
        
        if not safe_update:
            raise ValueError("No valid fields to update")
        
        # 添加更新时间
        safe_update["updated_at"] = datetime.utcnow()
        
        # 执行更新
        result = await db.avatars.update_one(
            {"_id": avatar_id, "user_id": user_id},
            {"$set": safe_update}
        )
        
        if result.matched_count == 0:
            # 未找到匹配文档
            return None
        
        # 清除缓存
        cache_key = f"avatar:{avatar_id}:{user_id}"
        await avatar_cache.delete(cache_key)
        
        # 获取更新后的对象
        return await self.get_avatar(avatar_id, user_id)
    
    async def update_avatar_image(
        self,
        avatar_id: int,
        user_id: int,
        image_data: bytes
    ) -> Avatar:
        """
        更新虚拟形象的图像
        
        :param avatar_id: 虚拟形象ID
        :param user_id: 用户ID，用于权限验证
        :param image_data: 新的图像二进制数据
        :return: 更新后的虚拟形象
        """
        db = await get_db()
        
        # 获取当前虚拟形象
        current_avatar = await self.get_avatar(avatar_id, user_id)
        if not current_avatar:
            return None
        
        # 1. 生成新的文件名和路径
        original_path = current_avatar.original_image_path
        file_ext = os.path.splitext(original_path)[1]
        if not file_ext:
            file_ext = ".jpg"  # 默认扩展名
        
        # 保持相同的文件路径，但添加版本号
        version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        new_filename = f"{os.path.splitext(os.path.basename(original_path))[0]}_{version}{file_ext}"
        new_path = os.path.join(os.path.dirname(original_path), new_filename)
        
        # 2. 保存新图像
        saved_path = await self.file_storage.save_file(image_data, new_path)
        
        # 3. 生成缩略图
        thumbnail_data = await self._generate_thumbnail(image_data)
        thumbnail_path = saved_path.replace(".", "_thumbnail.")
        thumbnail_saved_path = await self.file_storage.save_file(thumbnail_data, thumbnail_path)
        
        # 4. 更新数据库记录
        update_data = {
            "original_image_path": saved_path,
            "thumbnail_path": thumbnail_saved_path,
            "updated_at": datetime.utcnow(),
            "outdated_variants": current_avatar.generated_variants,  # 将现有变体标记为过时
            "generated_variants": [],  # 清空当前变体
            "processing_complete": False  # 需要重新处理
        }
        
        result = await db.avatars.update_one(
            {"_id": avatar_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            # 清理已上传文件
            await self.file_storage.delete_file(saved_path)
            await self.file_storage.delete_file(thumbnail_saved_path)
            return None
        
        # 5. 清除缓存
        cache_key = f"avatar:{avatar_id}:{user_id}"
        await avatar_cache.delete(cache_key)
        
        # 6. 返回更新后的对象
        return await self.get_avatar(avatar_id, user_id)
    
    async def update_avatar_tags(
        self,
        avatar_id: int,
        user_id: int,
        tags: List[str],
        operation: str = "replace"
    ) -> Avatar:
        """
        更新虚拟形象的标签
        
        :param avatar_id: 虚拟形象ID
        :param user_id: 用户ID，用于权限验证
        :param tags: 标签列表
        :param operation: 操作类型: replace, add, remove
        :return: 更新后的虚拟形象
        """
        db = await get_db()
        
        # 获取当前虚拟形象
        current_avatar = await self.get_avatar(avatar_id, user_id)
        if not current_avatar:
            return None
        
        # 根据操作类型处理标签
        update_query = {}
        if operation == "replace":
            # 替换所有标签
            update_query = {
                "$set": {
                    "tags": tags,
                    "updated_at": datetime.utcnow()
                }
            }
        elif operation == "add":
            # 添加新标签（避免重复）
            filtered_tags = [tag for tag in tags if tag not in current_avatar.tags]
            if filtered_tags:
                update_query = {
                    "$push": {"tags": {"$each": filtered_tags}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            else:
                # 没有新标签可添加
                return current_avatar
        elif operation == "remove":
            # 移除指定标签
            update_query = {
                "$pull": {"tags": {"$in": tags}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        else:
            raise ValueError(f"Invalid tag operation: {operation}")
        
        # 执行更新
        result = await db.avatars.update_one(
            {"_id": avatar_id, "user_id": user_id},
            update_query
        )
        
        if result.matched_count == 0:
            return None
        
        # 清除缓存
        cache_key = f"avatar:{avatar_id}:{user_id}"
        await avatar_cache.delete(cache_key)
        
        # 获取更新后的对象
        return await self.get_avatar(avatar_id, user_id)
    
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
