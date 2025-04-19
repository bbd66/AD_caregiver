from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pathlib import Path

class VoiceConfig(BaseModel):
    """语音服务全局配置"""
    api_key: str
    base_url: str = "https://api.siliconflow.cn/v1"
    default_voice: str = "FunAudioLLM/CosyVoice2-0.5B:alex"
    sample_rate: int = 16000
    cache_dir: Path = Path("audio_cache")

class VoiceSynthesisRequest(BaseModel):
    """语音合成请求模型"""
    text: str
    voice_model: str
    speed: float = 1.0
    emotion: Optional[str] = None
    output_format: str = "mp3"

class VoiceTrainingRequest(BaseModel):
    """语音训练请求模型"""
    audio_path: Path
    voice_name: str
    base_model: str = "FunAudioLLM/CosyVoice2-0.5B"
    training_text: str = "在一无所知中，梦里的一天结束了，一个新的轮回便会开始。"

class CustomVoiceProfile(BaseModel):
    """自定义音色配置"""
    name: str
    model_uri: str
    created_at: datetime = datetime.now()
    sample_count: int = 1
    last_used: Optional[datetime] = None
