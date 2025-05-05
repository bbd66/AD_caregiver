from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from schemas.voice import VoiceTrainRequest, VoiceTrainResponse, VoiceGenerateRequest, VoiceGenerateResponse
from services.voice import voice_service
from fastapi.responses import FileResponse  # 新增导入
from pathlib import Path  # 新增导入
import os  # 新增导入
import uuid  # 新增导入

router = APIRouter()

@router.post("/train/{digital_human_id}", response_model=VoiceTrainResponse)
async def train_custom_voice(
        background_tasks: BackgroundTasks,
        request: VoiceTrainRequest = None  
):
    try:
        result = await voice_service.upload_and_train(
            audio_url=request.audio_url,
            id=request.dh_id,
            custom_name=request.custom_name,
            model=request.model
        )

        return {
            "task_id": str(uuid.uuid4()),
            "status": "success",
            "message": "训练任务已提交"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{digital_human_id}", response_model=VoiceGenerateResponse) 
async def generate_voice_audio(request: VoiceGenerateRequest):
    try:
        result = await voice_service.generate_audio(
            audio_url=request.audio_url,
            id=request.dh_id,
            model_name="FunAudioLLM/CosyVoice2-0.5B"  # 添加默认模型名称
        )
        return {
            "audio_url": result["audio_url"],
            "duration": result.get("duration", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
