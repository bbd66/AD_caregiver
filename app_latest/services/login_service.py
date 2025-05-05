import logging
import hashlib
from typing import Tuple, Dict, Any

from models.db_models import User
from models.login.login_schema import LoginRequest, LoginResponse
from db.db_digital_manage import DatabaseManager

logger = logging.getLogger(__name__)

class LoginService:
    """登录服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        验证用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (成功状态, 用户数据, 消息)
        """
        try:
            # 加密密码
            hashed_password = self._hash_password(password)
            
            # 查询用户
            user = self.db_manager.get_user_by_username(username)
            
            if user and user.password == hashed_password:
                # 返回用户数据
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "bound_to_user_id": user.bound_to_user_id,
                    "email": user.email,
                    "phone": user.phone,
                    "created_at": user.created_at.isoformat()
                }
                return True, user_data, "登录成功"
            else:
                return False, {}, "用户名或密码错误"
            
        except Exception as e:
            logger.error(f"用户登录出错: {e}", exc_info=True)
            return False, {}, "用户登录时发生错误"
    
    def _hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        # 使用 SHA-256 加密（实际应用中建议使用更安全的算法如 bcrypt）
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        return sha256.hexdigest()