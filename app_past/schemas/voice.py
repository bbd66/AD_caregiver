from pydantic import BaseModel

class VoiceTrainRequest(BaseModel):
    model: str = "FunAudioLLM/CosyVoice2-0.5B"
    custom_name: str
    text: str

class VoiceTrainResponse(BaseModel):
    task_id: str
    status: str
    message: str

class VoiceGenerateRequest(BaseModel):
    text: str
    model_name: str

class VoiceGenerateResponse(BaseModel):
    audio_url: str
    duration: float 
