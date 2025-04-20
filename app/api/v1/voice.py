from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from schemas.voice import VoiceTrainRequest, VoiceTrainResponse, VoiceGenerateRequest, VoiceGenerateResponse
from services.voice import voice_service

router = APIRouter()

@router.post("/train", response_model=VoiceTrainResponse)
async def train_custom_voice(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        request: VoiceTrainRequest = None  #训练模型的功能之后再做
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

@router.post("/generate", response_model=VoiceGenerateResponse)
async def generate_voice_audio(request: VoiceGenerateRequest):
    try:
        result = await voice_service.generate_audio(
            text=request.text,
            model_name=request.model_name
        )
        return {"audio_url": result["audio_url"], "duration": result["duration"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
