from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from schemas.voice import VoiceTrainRequest, VoiceTrainResponse, VoiceGenerateRequest, VoiceGenerateResponse
from services.voice import voice_service
from fastapi.responses import FileResponse  # 新增导入
from pathlib import Path  # 新增导入
import os  # 新增导入

router = APIRouter()

# 新增存储路径配置
AUDIO_DIR = Path("audio_files") # 存储聊天音频的路径
AUDIO_DIR.mkdir(exist_ok=True)  # 确保目录存在

@router.post("/train/{digital_human_id}", response_model=VoiceTrainResponse)
async def train_custom_voice(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),      #音频文件
        request: VoiceTrainRequest = None  
):
    try:
        background_tasks.add_task(
            voice_service.upload_and_train,
            file,
            request.model,
            request.custom_name,
            request.text
        )
        return {"task_id": "generated_task_id", "status": "processing", "message": "Training started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{digital_human_id}", response_model=VoiceGenerateResponse)
async def generate_voice_audio(request: VoiceGenerateRequest):
    try:
        result = await voice_service.generate_audio(
            text=request.text,
            voice_uri=request.voice_uri
        )
        return {"audio_url": result["audio_url"], "duration": result["duration"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio/{digital_human_id}")             #这里涉及到如何获取到当前使用的数字人最新回复音频的问题，我觉得可能需要 数字人id、聊天id和时间戳 相关的数据，或者根据数字人第x次回复
async def get_audio_file(                            #的数据获取第x条音频记录？
    digital_human_id: str

    ):    
    """获取生成的音频文件"""
    file_path = AUDIO_DIR / f"{digital_human_id}.mp3" 
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"generated_audio_{digital_human_id}.mp3"
    )
