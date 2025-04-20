import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# 配置日志
logger = logging.getLogger("digital_manage_service")

# 设置路径
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

# 临时存储，用于在网络异常时创建本地ID
LOCAL_TEMP_DATA = {}

class DigitalManageService:
    """数字人管理服务，包含业务逻辑"""
    
    def create_digital_human(self, digital_human_data: Dict[str, Any], db) -> Tuple[bool, Dict[str, Any], str]:
        """
        创建新的数字人
        
        Args:
            digital_human_data: 数字人数据
            db: 数据库连接
            
        Returns:
            (成功状态, 创建的数据, 消息)
        """
        try:
            # 确保必要字段存在
            self._ensure_required_fields(digital_human_data)
            
            # 处理音频文件路径
            if 'original_reference_audio_path' in digital_human_data and digital_human_data['original_reference_audio_path']:
                reference_audio_url = self.copy_file_to_static(digital_human_data['original_reference_audio_path'], AUDIO_DIR)
                if reference_audio_url:
                    digital_human_data['referenceAudio'] = reference_audio_url
            
            if 'original_training_audio_path' in digital_human_data and digital_human_data['original_training_audio_path']:
                training_audio_url = self.copy_file_to_static(digital_human_data['original_training_audio_path'], AUDIO_DIR)
                if training_audio_url:
                    digital_human_data['trainingAudio'] = training_audio_url
            
            # 调用数据库方法添加数字人
            new_id = db.add_digital_human(digital_human_data)
            
            if not new_id:
                # 创建本地临时ID
                local_id = f"local-{int(time.time() * 1000)}"
                digital_human_data['id'] = local_id
                LOCAL_TEMP_DATA[local_id] = digital_human_data
                return True, digital_human_data, "创建数字人成功（本地模式）"
            
            # 获取创建的数字人数据
            created_human = db.get_digital_human(new_id)
            
            if created_human:
                self._ensure_required_fields(created_human)
                return True, created_human, "创建数字人成功"
            else:
                return False, {}, "无法获取创建的数字人数据"
                
        except Exception as e:
            logger.error(f"创建数字人出错: {e}", exc_info=True)
            
            # 创建一个本地临时ID
            local_id = f"local-{int(time.time() * 1000)}"
            digital_human_data['id'] = local_id
            LOCAL_TEMP_DATA[local_id] = digital_human_data
            
            return True, digital_human_data, "创建数字人成功（本地模式）"
    
    def get_digital_humans(self, skip: int, limit: int, search: Optional[str], db) -> Tuple[List[Dict[str, Any]], int]:
        """获取数字人列表，支持分页和搜索"""
        try:
            if search:
                # 使用搜索功能
                humans, total = db.search_digital_humans(search, skip, limit)
            else:
                # 使用分页功能
                humans, total = db.get_digital_humans_with_pagination(skip, limit)
            
            # 确保每条记录都有必要的字段
            for human in humans:
                self._ensure_required_fields(human)
            
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
            
            return humans, total
        
        except Exception as e:
            logger.error(f"获取数字人列表出错: {e}", exc_info=True)
            # 返回本地数据作为备份
            local_humans = list(LOCAL_TEMP_DATA.values())
            return local_humans, len(local_humans)
    
    def get_digital_human(self, digital_human_id: str, db) -> Tuple[bool, Dict[str, Any], str]:
        """获取单个数字人信息"""
        # 检查是否是本地临时ID
        if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
            local_data = LOCAL_TEMP_DATA[digital_human_id]
            self._ensure_required_fields(local_data)
            return True, local_data, "获取数字人成功（本地模式）"
        
        try:
            # 尝试从数据库获取
            human = db.get_digital_human(int(digital_human_id))
            
            if not human:
                return False, {}, f"ID为{digital_human_id}的数字人不存在"
            
            # 确保所有必要字段存在
            self._ensure_required_fields(human)
            return True, human, "获取数字人成功"
            
        except ValueError:
            # 如果ID不是整数也不是有效的本地ID
            return False, {}, f"无效的ID格式: {digital_human_id}"
        except Exception as e:
            logger.error(f"获取数字人信息出错: {e}", exc_info=True)
            return False, {}, "获取数字人信息时发生错误"
    
    def delete_digital_human(self, digital_human_id: str, db) -> Tuple[bool, str]:
        """删除数字人"""
        # 检查是否是本地临时ID
        if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
            # 从本地存储中删除
            del LOCAL_TEMP_DATA[digital_human_id]
            return True, f"成功删除ID为{digital_human_id}的数字人（本地模式）"
        
        try:
            # 先检查数字人是否存在
            existing_human = db.get_digital_human(int(digital_human_id))
            if not existing_human:
                return False, f"ID为{digital_human_id}的数字人不存在"
            
            # 删除数字人
            success = db.delete_digital_human(int(digital_human_id))
            
            if not success:
                return False, "删除数字人失败"
            
            return True, f"成功删除ID为{digital_human_id}的数字人"
            
        except ValueError:
            return False, f"无效的ID格式: {digital_human_id}"
        except Exception as e:
            logger.error(f"删除数字人出错: {e}", exc_info=True)
            return False, "删除数字人时发生错误"
    
    def update_digital_human(self, digital_human_id: str, update_data: Dict[str, Any], db) -> Tuple[bool, Dict[str, Any], str]:
        """更新数字人信息"""
        # 检查是否是本地临时ID
        if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
            # 更新本地数据
            for key, value in update_data.items():
                LOCAL_TEMP_DATA[digital_human_id][key] = value
            
            # 处理音频文件路径
            if 'original_reference_audio_path' in update_data and update_data['original_reference_audio_path']:
                reference_audio_url = self.copy_file_to_static(update_data['original_reference_audio_path'], AUDIO_DIR)
                if reference_audio_url:
                    LOCAL_TEMP_DATA[digital_human_id]['referenceAudio'] = reference_audio_url
            
            if 'original_training_audio_path' in update_data and update_data['original_training_audio_path']:
                training_audio_url = self.copy_file_to_static(update_data['original_training_audio_path'], AUDIO_DIR)
                if training_audio_url:
                    LOCAL_TEMP_DATA[digital_human_id]['trainingAudio'] = training_audio_url
            
            updated_data = LOCAL_TEMP_DATA[digital_human_id]
            self._ensure_required_fields(updated_data)
            
            return True, updated_data, "更新数字人成功（本地模式）"
        
        try:
            # 检查数字人是否存在
            existing_human = db.get_digital_human(int(digital_human_id))
            if not existing_human:
                return False, {}, f"ID为{digital_human_id}的数字人不存在"
            
            # 处理音频文件路径
            if 'original_reference_audio_path' in update_data and update_data['original_reference_audio_path']:
                reference_audio_url = self.copy_file_to_static(update_data['original_reference_audio_path'], AUDIO_DIR)
                if reference_audio_url:
                    update_data['referenceAudio'] = reference_audio_url
            
            if 'original_training_audio_path' in update_data and update_data['original_training_audio_path']:
                training_audio_url = self.copy_file_to_static(update_data['original_training_audio_path'], AUDIO_DIR)
                if training_audio_url:
                    update_data['trainingAudio'] = training_audio_url
            
            # 调用数据库更新方法
            success = db.update_digital_human(int(digital_human_id), update_data)
            if not success:
                return False, {}, "更新数字人失败"
            
            # 获取更新后的数据
            updated_human = db.get_digital_human(int(digital_human_id))
            if not updated_human:
                return False, {}, "获取更新后的数字人信息失败"
            
            # 确保所有必要字段存在
            self._ensure_required_fields(updated_human)
            return True, updated_human, "更新数字人成功"
            
        except ValueError:
            return False, {}, f"无效的ID格式: {digital_human_id}"
        except Exception as e:
            logger.error(f"更新数字人信息出错: {e}", exc_info=True)
            return False, {}, "更新数字人信息时发生错误"
    
    def copy_file_to_static(self, file_path, target_dir):
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
    
    def _ensure_required_fields(self, data: Dict[str, Any]):
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

# 创建服务实例
digital_manage_service = DigitalManageService() 
