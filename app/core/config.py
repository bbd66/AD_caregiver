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
    SILICONFLOW_API_KEY: str                   # Required
    SILICONFLOW_BASE_URL: HttpUrl = "https://api.siliconflow.cn/v1"
    DEFAULT_VOICE_MODEL: str = "FunAudioLLM/CosyVoice2-0.5B"
    DEFAULT_VOICE_NAME: str = "alex"           # alex | custom voices
    VOICE_CACHE_DIR: str = "./voice_cache"     # Store generated audio files

    # ==================== #
    #  Chat Engine Config   #
    # ==================== #
    DEEPSEEK_API_KEY: str                      # Required
    DEEPSEEK_API_URL: HttpUrl = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    CHAT_HISTORY_LIMIT: int = 10               # Max conversation turns

    # ==================== #
    #    Database Config    #
    # ==================== #
    DATABASE_URI: str = "sqlite:///./digital_human.db"
    DATABASE_ECHO: bool = False                # SQLAlchemy query logging
    DATABASE_POOL_SIZE: int = 5

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
