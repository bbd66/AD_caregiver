from fastapi import APIRouter, HTTPException
from schemas.deepseek import DeepSeekRequest, DeepSeekResponse
from services.deepseek import deepseek_service

router = APIRouter()

@router.post("/chat", response_model=DeepSeekResponse)
async def chat_with_deepseek(request: DeepSeekRequest):
    try:
        reply = await deepseek_service.get_response(request.user_input)
        return {"reply": reply}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))