from pydantic import BaseModel, Field
from typing import Optional, List, Union


class DigitalHumanBase(BaseModel):
    """数字人基础模型"""
    name: str = Field(..., description="数字人名称")
    phone: Optional[str] = Field(None, description="联系电话")
    description: Optional[str] = Field(None, description="描述信息")
    avatar: Optional[str] = Field(None, description="头像路径", alias="image_path")
    referenceAudio: Optional[str] = Field(None, description="参考音频路径", alias="reference_audio_path")
    trainingAudio: Optional[str] = Field(None, description="训练音频路径", alias="train_audio_path")
    referenceAudioLength: Optional[str] = Field(None, description="参考音频长度")
    trainingAudioLength: Optional[str] = Field(None, description="训练音频长度")


class DigitalHumanCreate(DigitalHumanBase):
    """创建数字人的请求模型"""
    pass


class DigitalHuman(DigitalHumanBase):
    """数字人响应模型，包含ID"""
    id: Union[int, str] = Field(..., description="数字人ID，可以是数字或字符串")

    class Config:
        from_attributes = True


class DigitalHumanList(BaseModel):
    """数字人列表响应模型"""
    items: List[DigitalHuman]
    total: int


class ResponseBase(BaseModel):
    """API响应基础模型"""
    success: bool
    message: str


class DigitalHumanResponse(ResponseBase):
    """单个数字人响应模型"""
    data: Optional[DigitalHuman] = None


class DigitalHumanListResponse(ResponseBase):
    """数字人列表响应模型"""
    data: Optional[DigitalHumanList] = None 