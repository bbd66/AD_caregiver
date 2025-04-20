import httpx
from fastapi import UploadFile
from core.config import settings

class VoiceService:
    def __init__(self):
        self.api_url = settings.TTS_BASE_URL
        self.headers = {"Authorization": f"Bearer {settings.TTS_API_KEY}"}

    async def upload_and_train(self, file: UploadFile, model: str, custom_name: str, text: str) -> dict:
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            data = {"model": model, "customName": custom_name, "text": text}
            response = await client.post(
                f"{self.api_url}/uploads/audio/voice",
                headers=self.headers,
                files=files,
                data=data
            )
            if response.status_code != 200:
                raise Exception(f"Training failed: {response.text}")
            return response.json()

    async def generate_audio(self, text: str, model_name: str) -> dict:
        async with httpx.AsyncClient() as client:
            data = {"text": text, "model": model_name}
            response = await client.post(
                f"{self.api_url}/synthesize/audio",
                headers=self.headers,
                json=data
            )
            if response.status_code != 200:
                raise Exception(f"Generation failed: {response.text}")
            return response.json()

voice_service = VoiceService()
