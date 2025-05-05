import logging
import hashlib
from typing import Tuple, Dict, Any
from typing import Optional
from models.db_models import User
from models.register import UserCreate, UserResponse
from db.db_digital_manage import DatabaseManager
import datetime

logger = logging.getLogger(__name__)

class RegisterService:
    """注册服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_user(self, user_data: UserCreate) -> Tuple[bool, Dict[str, Any], str]:
        """
        创建新用户
        
        Args:
            user_data: 用户注册信息
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (成功状态, 用户数据, 消息)
        """
        try:
            logger.info(f"开始创建用户: {user_data.username}, 角色: {user_data.role}")
            
            # 验证用户数据
            if self._check_username_exists(user_data.username):
                logger.warning(f"用户名已存在: {user_data.username}")
                return False, {}, "用户名已存在"
                
            # 检查邮箱是否已存在
            if self._check_email_exists(user_data.email):
                logger.warning(f"邮箱已存在: {user_data.email}")
                return False, {}, "邮箱已被注册"
                
            # 检查手机号是否已存在
            if self._check_phone_exists(user_data.phone):
                logger.warning(f"手机号已存在: {user_data.phone}")
                return False, {}, "手机号已被注册"
                
            if not self._validate_user_data(user_data):
                logger.warning(f"用户数据验证失败: {user_data}")
                return False, {}, "注册信息无效"
            
            # 处理管理员绑定逻辑
            bound_user_id = None
            if user_data.role == 1:  # 管理员
                logger.info(f"处理管理员绑定逻辑: {user_data.bound_username}")
                if not user_data.bound_username:
                    logger.warning("管理员未提供绑定用户名")
                    return False, {}, "管理员必须绑定患者用户名"
                
                # 根据用户名查询患者ID
                bound_user = self._get_user_by_username(user_data.bound_username)
                logger.info(f"查询绑定用户结果: {bound_user}")
                
                if not bound_user:
                    logger.warning(f"绑定的患者不存在: {user_data.bound_username}")
                    return False, {}, "绑定的患者不存在"
                
                # 确保角色是整数
                bound_user_role = bound_user.role
                if isinstance(bound_user_role, str):
                    bound_user_role = int(bound_user_role)
                logger.info(f"绑定用户角色: {bound_user_role}, 角色类型: {type(bound_user_role)}")
                    
                if bound_user_role != 0:
                    logger.warning(f"绑定的用户不是患者: {user_data.bound_username}, 角色: {bound_user_role}")
                    return False, {}, "绑定的用户不是患者"
                
                bound_user_id = bound_user.id
                logger.info(f"成功获取绑定用户ID: {bound_user_id}")
            
            # 加密密码
            hashed_password = self._hash_password(user_data.password)
            
            # 创建用户数据字典
            user_dict = {
                "username": user_data.username,
                "password": hashed_password,
                "email": user_data.email,
                "phone": user_data.phone,
                "role": int(user_data.role),  # 确保角色是整数
                "bound_to_user_id": bound_user_id
            }
            
            logger.info(f"准备创建用户数据: {user_dict}")
            
            # 调用数据库方法创建用户
            user_id = self.db_manager.add_user(user_dict)
            
            if user_id:
                # 返回创建的用户数据
                created_user = {
                    "id": user_id,
                    "username": user_data.username,
                    "email": user_data.email,
                    "phone": user_data.phone,
                    "role": int(user_data.role),  # 确保角色是整数
                    "bound_to_user_id": bound_user_id,
                    "created_at": datetime.datetime.utcnow().isoformat()
                }
                logger.info(f"用户创建成功: {created_user}")
                return True, created_user, "用户注册成功"
            else:
                logger.error("数据库返回的用户ID为空")
                return False, {}, "用户注册失败"
            
        except Exception as e:
            logger.error(f"用户注册出错: {str(e)}", exc_info=True)
            return False, {}, f"用户注册时发生错误: {str(e)}"
    
    def _check_username_exists(self, username: str) -> bool:
        """检查用户名是否已存在"""
        return self.db_manager.get_user_by_username(username) is not None

    def _check_email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        return self.db_manager.get_user_by_email(email) is not None

    def _check_phone_exists(self, phone: str) -> bool:
        """检查手机号是否已存在"""
        return self.db_manager.get_user_by_phone(phone) is not None

    def _get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名查询用户"""
        user = self.db_manager.get_user_by_username(username)
        if user:
            logger.info(f"找到用户: {user.username}, 角色: {user.role}, 角色类型: {type(user.role)}")
            # 确保角色是整数
            if isinstance(user.role, str):
                user.role = int(user.role)
            logger.info(f"处理后的角色: {user.role}, 角色类型: {type(user.role)}")
        else:
            logger.warning(f"未找到用户: {username}")
        return user
    
    def _validate_user_data(self, user_data: UserCreate) -> bool:
        """验证用户注册数据"""
        logger.info("开始验证用户数据...")
        
        # 验证用户名长度
        if len(user_data.username) < 3 or len(user_data.username) > 50:
            logger.warning(f"用户名长度验证失败: {len(user_data.username)}")
            return False
        logger.info("用户名长度验证通过")
        
        # 验证密码长度
        if len(user_data.password) < 6 or len(user_data.password) > 50:
            logger.warning(f"密码长度验证失败: {len(user_data.password)}")
            return False
        logger.info("密码长度验证通过")
        
        # 验证角色
        if user_data.role not in [0, 1]:
            logger.warning(f"角色验证失败: {user_data.role}")
            return False
        logger.info("角色验证通过")
            
        # 验证邮箱格式
        if not self._is_valid_email(user_data.email):
            logger.warning(f"邮箱格式验证失败: {user_data.email}")
            return False
        logger.info("邮箱格式验证通过")
            
        # 验证手机号格式
        if not self._is_valid_phone(user_data.phone):
            logger.warning(f"手机号格式验证失败: {user_data.phone}")
            return False
        logger.info("手机号格式验证通过")
        
        logger.info("所有验证通过")
        return True

    def _is_valid_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        logger.info(f"邮箱验证结果: {email} -> {is_valid}")
        return is_valid

    def _is_valid_phone(self, phone: str) -> bool:
        """验证手机号格式"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        is_valid = bool(re.match(pattern, phone))
        logger.info(f"手机号验证结果: {phone} -> {is_valid}")
        return is_valid
    
    def _hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        # 使用 SHA-256 加密（实际应用中建议使用更安全的算法如 bcrypt）
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        return sha256.hexdigest()