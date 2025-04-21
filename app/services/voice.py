import io
import httpx
from fastapi import UploadFile
from fastapi import HTTPException
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import datetime
from core.config import settings
from web_app import app, get_all_digital_humans, get_digital_human, save_audio_to_database, save_chat_to_database, Document
from vosk import Model, KaldiRecognizer
import wave
import json
from .deepseek import deepseek_service
from db import app_db
from typing import Optional
import aiofiles  
from openai import OpenAI
from openai import AsyncOpenAI
import asyncio 

class VoiceService:
    def __init__(self):
        self.api_url = settings.TTS_BASE_URL
        self.headers = {"Authorization": f"Bearer {settings.TTS_API_KEY}"}
    
    async def transcribe_audio_file(self, audio_path: str)-> str:
        #加载Vosk模型
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建模型路径（假设模型文件夹在 voice.py 同级目录）
        model_path = os.path.join(current_dir, "vosk-model-small-cn-0.22")
        model = Model(model_path )  
        full_text = []
 
        #下载文件
        file_content = await self._read_local_file(audio_path)
        
        # 验证并获取文件类型
        content_type = self._validate_audio_file(file_content)
        
        # 生成唯一文件名
        file_ext = self._get_file_extension(content_type)
        unique_name = f"train_{uuid.uuid4()}_{int(time.time())}{file_ext}"

        audio_bytes = io.BytesIO(file_content)
    
        # 2. 打开音频文件
        # with wave.open(audio_bytes, "rb") as wf:
        #     if wf.getnchannels() != 1:
        #         raise ValueError("需要单声道音频")
        #     if wf.getsampwidth() != 2:
        #         raise ValueError("需要16-bit位深")
        #     if wf.getframerate() != 16000:
        #         raise ValueError("需要16kHz采样率")

        # # 4. 创建识别器
        sample_rate = 16000
        recognizer = KaldiRecognizer(model, sample_rate)
        
        # while True:
        #         data = wf.readframes(4000)
        #         if not data:
        #             break
        #         if recognizer.AcceptWaveform(data):
        #             result = json.loads(recognizer.Result())
        #             full_text.append(result.get("text", ""))

        # final_result = json.loads(recognizer.FinalResult())
        # full_text.append(final_result.get("text", ""))

        # return "".join(full_text)
           
        if recognizer.AcceptWaveform(file_content):      # 关键识别调用
            result = json.loads(recognizer.Result())   # 获取识别结果
            text = result.get('text', '')  # 提取文本内容，文件类型为txt
        
        return text

    
    async def upload_and_train(self, model: str, custom_name: str, id: int,audio_url:str) -> dict:
        
        
        file_content = await self._read_local_file(audio_url)
        
        # 验证并获取文件类型
        content_type = self._validate_audio_file(file_content)
        
        # 生成唯一文件名
        file_ext = self._get_file_extension(content_type)
        unique_name = f"train_{uuid.uuid4()}_{int(time.time())}{file_ext}"
        
       
        async with httpx.AsyncClient() as client:

            files = {"file": (unique_name, file_content, content_type)}
            data = {"model": model, "customName": custom_name, "text": "在一无所知中，梦里的一天结束了，一个新的轮回便会开始。"}
            response = await client.post(
                f"{self.api_url}/uploads/audio/voice",
                headers=self.headers,
                files=files,
                data=data
            )
            if response.status_code != 200:
                raise Exception(f"Training failed: {response.text}")
            
            uri=response.json()['uri']

            db_manager = app_db.DatabaseManager()
            db_manager.update_digital_human(
            digital_human_id=id,
            update_data={'video_path': uri}
            )

            return response.json()

    async def generate_audio(self, audio_url:str , id:str, model_name: str) -> dict:  #self, text: str, model_name: str  audio_url:str,id:str
        async with httpx.AsyncClient() as client:

            final_result =  await self.transcribe_audio_file(audio_url)#识别成文字

            text_res=await deepseek_service.get_response(final_result)#接入ds得到回答
            
            voice_uri=get_digital_human(id)

            data = {"text": text_res, "model": model_name}
            client =  AsyncOpenAI(
            api_key="sk-swldhdfbzrwtesarrhxwbovcivpzezfshaxvcxrtwvdzylss", # 从 https://cloud.siliconflow.cn/account/ak 获取
            base_url="https://api.siliconflow.cn/v1"
            )

            # with client.audio.speech.with_streaming_response.create(
            #       model=model_name, # 支持 fishaudio / GPT-SoVITS / CosyVoice2-0.5B 系列模型
            #       voice="FunAudioLLM/CosyVoice2-0.5B:alex", # 用户上传音色名称，参考
            #       # 用户输入信息
            #       input=text_res,
            #       response_format="mp3"
            #     ) as response:
            #         #response.stream_to_file(speech_file_path)

            # response = await client.audio.speech.with_streaming_response.create(
            # model=model_name,
            # voice="FunAudioLLM/CosyVoice2-0.5B:alex",
            # input=text_res,
            # response_format="mp3"
            # )
            async with client.audio.speech.with_streaming_response.create(
            model=model_name,
            voice=voice_uri['video_path'],#"FunAudioLLM/CosyVoice2-0.5B:alex"
            input=text_res,
            response_format="mp3"
             ) as response:  
             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
             filename = f"speech_{timestamp}.mp3"
             relative_path = f"/static/uploads/digital_humans/audio/{filename}"
             absolute_path = os.path.abspath(relative_path) 
             #response.stream_to_file(relative_path)
             async with aiofiles.open(relative_path, "wb") as f:
                 async for chunk in response.iter_bytes():
                     await f.write(chunk)

            if not await asyncio.to_thread(os.path.exists, absolute_path):
                    raise HTTPException(500, "文件保存失败")

            result = save_audio_to_database(
                    filename=filename,
                    filepath=relative_path,
                    digital_human_id=id,
                )
            if not result["success"]:
                print(f"音频保存到数据库失败: {result.get('error', '未知错误')}")
            
            return relative_path
    
    async def _read_local_file(self, file_path: str, max_size: int = 50 * 1024 * 1024) -> bytes:
        """从本地路径读取音频文件内容"""
        try:
            # 检查文件是否存在
            if not os.path.isfile(file_path):
                raise HTTPException(status_code=404, detail="音频文件不存在")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"音频文件过大 ({file_size//1024//1024}MB)，最大支持{max_size//1024//1024}MB"
                )
            
            # 异步读取文件内容
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return content
        
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"读取音频文件失败: {str(e)}"
            )

    async def _download_audio_from_url(self, url: str, max_size: int = 50 * 1024 * 1024) -> bytes:
        """专用音频下载方法"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=30)
                response.raise_for_status()
                
                # 验证文件大小
                content_length = int(response.headers.get('Content-Length', 0))
                if content_length > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"音频文件过大 ({content_length//1024//1024}MB)，最大支持{max_size//1024//1024}MB"
                    )
                
                return response.content
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"无法下载音频文件: {e.response.status_code} {e.response.reason_phrase}"
            )

    def _validate_audio_file(self, content: bytes) -> str:
        """验证音频文件类型"""
        header = content[:32]
    
        # WAV文件头
        if header.startswith(b'RIFF') and b'WAVE' in header:
            return "audio/wav"
    
    # MP3文件头（ID3或帧同步）
        if header.startswith(b'ID3') or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            return "audio/mpeg"
    
        raise HTTPException(
            status_code=415,
            detail="不支持的音频格式，仅接受WAV/MP3文件"
        )

    def _get_file_extension(self, content_type: str) -> str:
        """根据类型获取扩展名"""
        return {
            "audio/wav": ".wav",
            "audio/mpeg": ".mp3"
        }.get(content_type, ".bin")

voice_service = VoiceService()
