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
#from web_app import app, get_all_digital_humans, get_digital_human, save_audio_to_database, save_chat_to_database, Document
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
        self.output_dir = "/static/document"
    
    async def transcribe_audio_file(self, audio_path: str)-> str:
        """从音频文件转录文本"""
        try:
            # 加载Vosk模型
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "vosk-model-small-cn-0.22")
            model = Model(model_path)
            full_text = []

            # 下载文件
            file_content = await self._read_local_file(audio_path)
            
            # 验证并获取文件类型
            content_type = self._validate_audio_file(file_content)
            
            # 生成唯一文件名
            file_ext = self._get_file_extension(content_type)
            unique_name = f"train_{uuid.uuid4()}_{int(time.time())}{file_ext}"

            # 使用pydub处理音频
            try:
                from pydub import AudioSegment
                import io
                
                # 将音频数据转换为AudioSegment对象
                if content_type == "audio/wav":
                    audio = AudioSegment.from_wav(io.BytesIO(file_content))
                else:  # mp3
                    audio = AudioSegment.from_mp3(io.BytesIO(file_content))
                
                # 转换为16kHz采样率
                audio = audio.set_frame_rate(16000)
                # 转换为单声道
                audio = audio.set_channels(1)
                
                # 导出为WAV格式
                wav_io = io.BytesIO()
                audio.export(wav_io, format="wav")
                wav_io.seek(0)
                file_content = wav_io.read()
                
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="请安装pydub库以支持音频处理: pip install pydub"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"音频处理失败: {str(e)}"
                )

            # 创建识别器
            sample_rate = 16000
            recognizer = KaldiRecognizer(model, sample_rate)
            
            # 处理音频数据
            with wave.open(io.BytesIO(file_content), 'rb') as wf:
                while True:
                    data = wf.readframes(4000)
                    if not data:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        full_text.append(result.get("text", ""))

            final_result = json.loads(recognizer.FinalResult())
            full_text.append(final_result.get("text", ""))
            
            final_text = "".join(full_text)
            # 处理空格
            final_text = final_text.replace(" ", "")
            
            if not final_text:
                raise HTTPException(
                    status_code=400,
                    detail="未能识别出任何文本，请确保音频清晰且包含语音内容"
                )

            return final_text
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"语音识别失败: {str(e)}"
            )

    
    async def upload_and_train(self, model: str, custom_name: str, id: int,audio_url:str) -> dict:
        
        
        file_content = await self._read_local_file(audio_url)
        
        # 验证并获取文件类型
        content_type = self._validate_audio_file(file_content)
        
        # 生成唯一文件名
        file_ext = self._get_file_extension(content_type)
        unique_name = f"train_{uuid.uuid4()}_{int(time.time())}{file_ext}"
        
       
        async with httpx.AsyncClient() as client:

            files = {"file": (unique_name, file_content, content_type)}
            data = {"model": model, "customName": custom_name, "text": "你好，请问今天的天气怎么样？"}
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

    async def generate_audio(self, audio_url:str , id:str, model_name: str) -> dict:
        async with httpx.AsyncClient() as client:
            db_manager = app_db.DatabaseManager()
            digital_human = db_manager.get_digital_human(id)
            if not digital_human:
                raise HTTPException(status_code=404, detail="数字人不存在")
            
            description = digital_human.get('description', '')
            video_path = digital_human.get('video_path')
            if not video_path:
                raise HTTPException(status_code=400, detail="数字人未完成训练，请先训练音色")

            final_result = await self.transcribe_audio_file(audio_url)  # 识别成文字
            if not final_result:
                raise HTTPException(status_code=400, detail="语音识别失败")

            db_manager.save_chat_to_database(final_result, id)  # 把记录存入库中

            text_res = await deepseek_service.get_response(description, final_result)  # 接入ds得到回答
            if not text_res:
                raise HTTPException(status_code=500, detail="获取AI回复失败")

            db_manager.save_chat_to_database(text_res, id)  # 把记录存入库中

            client = AsyncOpenAI(
                api_key="sk-swldhdfbzrwtesarrhxwbovcivpzezfshaxvcxrtwvdzylss",
                base_url="https://api.siliconflow.cn/v1"
            )

            try:
                async with client.audio.speech.with_streaming_response.create(
                    model=model_name,
                    voice=video_path,
                    input=text_res,
                    response_format="mp3"
                ) as response:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"speech_{timestamp}.mp3"
                    
                    # 确保输出目录存在
                    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                            "static", "uploads", "digital_humans", "audio")
                    os.makedirs(output_dir, exist_ok=True)
                    
                    relative_path = f"/static/uploads/digital_humans/audio/{filename}"
                    absolute_path = os.path.join(output_dir, filename)
                    
                    async with aiofiles.open(absolute_path, "wb") as f:
                        async for chunk in response.iter_bytes():
                            await f.write(chunk)

                if not await asyncio.to_thread(os.path.exists, absolute_path):
                    raise HTTPException(500, "文件保存失败")
                
                result = db_manager.save_audio_to_database(
                    filename=filename,
                    filepath=relative_path,
                    digital_human_id=id,
                )
                if not result["success"]:
                    print(f"音频保存到数据库失败: {result.get('error', '未知错误')}")
                
                return {
                    "audio_url": relative_path,
                    "duration": 0.0  # 暂时返回0，后续可以添加音频时长计算
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"语音生成失败: {str(e)}")
    
    async def _read_local_file(self, file_path: str, max_size: int = 50 * 1024 * 1024) -> bytes:
        """从本地路径读取音频文件内容"""
        try:
            # 处理URL路径
            if file_path.startswith('http'):
                async with httpx.AsyncClient() as client:
                    response = await client.get(file_path)
                    if response.status_code != 200:
                        raise HTTPException(status_code=404, detail=f"无法下载音频文件: {file_path}")
                    return response.content

            # 处理本地文件路径
            if file_path.startswith('/'):
                file_path = file_path[1:]  # 移除开头的斜杠
            
            # 获取当前工作目录
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(current_dir, file_path)
            
            # 检查文件是否存在
            if not os.path.isfile(full_path):
                raise HTTPException(status_code=404, detail=f"音频文件不存在: {file_path}")
            
            # 获取文件大小
            file_size = os.path.getsize(full_path)
            if file_size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"音频文件过大 ({file_size//1024//1024}MB)，最大支持{max_size//1024//1024}MB"
                )
            
            # 异步读取文件内容
            async with aiofiles.open(full_path, 'rb') as f:
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