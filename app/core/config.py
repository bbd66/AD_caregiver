import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator, HttpUrl

class Settings(BaseSettings):
    """Application Settings (Load from .env)"""

    # ==================== #
    #      Core Config      #
    # ==================== #
    APP_NAME: str = "DeepSeek Chat"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    API_V1_STR: str = "/api/v1"

    # ==================== #
    #   Voice Service Config  #
    # ==================== #
   TTS_API_KEY = "sk-swldhdfbzrwtesarrhxwbovcivpzezfshaxvcxrtwvdzylss"
   TTS_BASE_URL = "https://api.siliconflow.cn/v1"


    # ==================== #
    #  Chat Engine Config   #
    # ==================== #
    DEEPSEEK_API_KEY = "sk-7d54d72c0a314c45ae838b4ea422d152"   
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


    # ==================== #
    #    Database Config    #
    # ==================== #
    DATABASE_URI = "mysql+pymysql://root:@localhost/app_db"


    # ==================== #
    #      CORS Config      #
    # ==================== #
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
