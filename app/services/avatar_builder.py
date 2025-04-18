#虚拟形象的实现逻辑 反应逻辑

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
