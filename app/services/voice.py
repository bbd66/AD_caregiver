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
import numpy as np
from scipy import signal
 
class VoiceService:
    def __init__(self):
        self.api_url = settings.TTS_BASE_URL
        self.headers = {"Authorization": f"Bearer {settings.TTS_API_KEY}"}
    
    async def transcribe_audio_file(self, audio_path: str)-> str:
        try:
            #加载Vosk模型
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 构建模型路径（假设模型文件夹在 voice.py 同级目录）
            model_path = os.path.join(current_dir, "vosk-model-small-cn-0.22")
            logging.info(f"加载语音识别模型: {model_path}")
            if not os.path.exists(model_path):
                raise HTTPException(status_code=500, detail="语音识别模型不存在")
            
            # 检查模型文件
            model_files = os.listdir(model_path)
            logging.info(f"模型文件列表: {model_files}")
            
            model = Model(model_path)  
            full_text = []
 
            #下载文件
            logging.info(f"开始读取音频文件: {audio_path}")
            
            # 处理文件路径
            if audio_path.startswith('http://') or audio_path.startswith('https://'):
                # 从URL中提取文件路径
                if '/static/' in audio_path:
                    # 提取/static/后面的部分
                    audio_path = audio_path.split('/static/')[-1]
                    logging.info(f"从URL提取的文件路径: {audio_path}")
                else:
                    raise HTTPException(status_code=400, detail="无效的音频文件URL")
            
            # 构建完整的文件路径
            base_dir = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(base_dir, 'static', audio_path.lstrip('/'))
            logging.info(f"处理后的音频文件路径: {full_path}")
            
            if not os.path.exists(full_path):
                # 尝试在audio目录下查找
                audio_path = os.path.join(base_dir, 'static', 'audio', os.path.basename(audio_path))
                logging.info(f"尝试在audio目录下查找文件: {audio_path}")
                
                if os.path.isfile(audio_path):
                    full_path = audio_path
                else:
                    logging.error(f"文件不存在: {full_path} 或 {audio_path}")
                    raise HTTPException(status_code=404, detail=f"音频文件不存在: {os.path.basename(audio_path)}")
            
            file_content = await self._read_local_file(full_path)
            logging.info(f"成功读取音频文件，大小: {len(file_content)} 字节")
            
            # 验证并获取文件类型
            content_type = self._validate_audio_file(file_content)
            logging.info(f"音频文件类型: {content_type}")
            
            # 生成唯一文件名
            file_ext = self._get_file_extension(content_type)
            unique_name = f"train_{uuid.uuid4()}_{int(time.time())}{file_ext}"
            logging.info(f"生成临时文件名: {unique_name}")

            # 创建音频字节流
            audio_bytes = io.BytesIO(file_content)
    
            # 使用wave模块打开音频文件
            with wave.open(audio_bytes, 'rb') as wf:
                # 获取原始音频参数
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes = wf.getnframes()
                logging.info(f"原始音频参数: 声道数={channels}, 采样宽度={sampwidth}, 采样率={framerate}, 帧数={nframes}")
                
                # 检查音频参数是否在合理范围内
                if nframes == 0:
                    raise HTTPException(status_code=400, detail="音频文件为空")
                if framerate < 8000 or framerate > 48000:
                    raise HTTPException(status_code=400, detail=f"不支持的采样率: {framerate}")
                
                # 读取所有音频数据
                audio_data = wf.readframes(nframes)
                logging.info(f"读取音频数据: {len(audio_data)} 字节")
                
                # 转换为numpy数组以便处理
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                logging.info(f"转换为numpy数组: shape={audio_array.shape}, dtype={audio_array.dtype}")
                
                # 如果不是单声道，转换为单声道
                if channels != 1:
                    logging.info("转换音频为单声道")
                    audio_array = audio_array.reshape(-1, channels)
                    audio_array = audio_array.mean(axis=1).astype(np.int16)
                    logging.info(f"转换后数组: shape={audio_array.shape}, dtype={audio_array.dtype}")
                    audio_data = audio_array.tobytes()
                    logging.info(f"转换后音频数据: {len(audio_data)} 字节")
                
                # 如果不是16kHz，重采样
                if framerate != 16000:
                    logging.info("重采样音频到16kHz")
                    audio_array = signal.resample(audio_array, int(len(audio_array) * 16000 / framerate))
                    audio_array = (audio_array * 32767).astype(np.int16)
                    logging.info(f"重采样后数组: shape={audio_array.shape}, dtype={audio_array.dtype}")
                    audio_data = audio_array.tobytes()
                    logging.info(f"重采样后音频数据: {len(audio_data)} 字节")

                # 创建新的音频字节流
                output = io.BytesIO()
                with wave.open(output, 'wb') as wf_out:
                    wf_out.setnchannels(1)  # 单声道
                    wf_out.setsampwidth(2)  # 16-bit
                    wf_out.setframerate(16000)  # 16kHz
                    wf_out.writeframes(audio_data)
                    logging.info(f"写入转换后的音频数据: {len(audio_data)} 字节")
                
                # 验证转换后的音频参数
                output.seek(0)
                with wave.open(output, 'rb') as wf_check:
                    check_channels = wf_check.getnchannels()
                    check_sampwidth = wf_check.getsampwidth()
                    check_framerate = wf_check.getframerate()
                    check_nframes = wf_check.getnframes()
                    logging.info(f"转换后音频参数: 声道数={check_channels}, 采样宽度={check_sampwidth}, 采样率={check_framerate}, 帧数={check_nframes}")
                
                # 重置指针位置
                output.seek(0)
                
                # 创建识别器
                sample_rate = 16000
                recognizer = KaldiRecognizer(model, sample_rate)
                
                # 读取转换后的音频数据
                with wave.open(output, 'rb') as wf_in:
                    chunk_size = 4000
                    total_chunks = 0
                    processed_chunks = 0
                    while True:
                        data = wf_in.readframes(chunk_size)
                        if not data:
                            break
                        total_chunks += 1
                        if recognizer.AcceptWaveform(data):
                            processed_chunks += 1
                            result = json.loads(recognizer.Result())
                            text = result.get("text", "")
                            if text:
                                full_text.append(text)
                                logging.info(f"识别到文本: {text}")

                    final_result = json.loads(recognizer.FinalResult())
                    final_text = final_result.get("text", "")
                    if final_text:
                        full_text.append(final_text)
                        logging.info(f"最终识别文本: {final_text}")
                    
                    logging.info(f"处理了 {total_chunks} 个音频块，成功识别 {processed_chunks} 个块")

            result_text = "".join(full_text)
            if not result_text:
                logging.warning("语音识别结果为空")
                raise HTTPException(status_code=400, detail="未能识别出任何文本，请检查音频质量")
            
            logging.info(f"语音识别完成，总文本长度: {len(result_text)}")
            return result_text
            
        except HTTPException as e:
            logging.error(f"语音识别失败: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"语音识别失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"语音识别失败: {str(e)}"
            )

    async def upload_and_train(self, model: str, custom_name: str, id: int, audio_url: str) -> dict:
        try:
            # 判断是本地文件还是URL
            if audio_url.startswith('http'):
                file_content = await self._download_audio_from_url(audio_url)
            else:
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
                
                uri = response.json()['uri']

                db_manager = app_db.DatabaseManager()
                db_manager.update_digital_human(
                    digital_human_id=id,
                    update_data={'video_path': uri}
                )

            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def generate_audio(self, audio_url:str , id:str, model_name: str) -> dict:
        try:
            # 记录输入参数
            logging.info("===== generate_audio 方法开始 =====")
            logging.info(f"输入参数: audio_url={audio_url}, id={id}, model_name={model_name}")
            
            async with httpx.AsyncClient() as client:
                # 1. 转录音频
                logging.info(f"开始转录音频文件: {audio_url}")
                final_result = await self.transcribe_audio_file(audio_url)
                if not final_result:
                    logging.error("音频转写结果为空")
                    raise HTTPException(status_code=400, detail="音频转写结果为空")
                logging.info(f"音频转写结果: {final_result}")

                # 2. 获取AI回复
                logging.info("开始获取AI回复")
                logging.info(f"发送到deepseek的文本: {final_result}")
                text_res = await deepseek_service.get_response(final_result)
                if not text_res:
                    logging.error("AI回复为空")
                    raise HTTPException(status_code=400, detail="AI回复为空")
                logging.info(f"AI回复内容: {text_res}")

                # 3. 获取数字人信息
                logging.info(f"获取数字人信息: id={id}")
                db_manager = app_db.DatabaseManager()
                digital_human = db_manager.get_digital_human(id)
                if not digital_human:
                    logging.error(f"数字人不存在: id={id}")
                    raise HTTPException(status_code=404, detail="数字人不存在")
                
                if not digital_human.get('video_path'):
                    logging.error(f"数字人音色未设置: id={id}")
                    raise HTTPException(status_code=400, detail="数字人音色未设置")
                
                logging.info(f"使用数字人音色: {digital_human['video_path']}")

                # 4. 生成语音
                logging.info("开始生成语音")
                logging.info(f"使用模型: {model_name}")
                logging.info(f"使用音色: {digital_human['video_path']}")
                logging.info(f"生成文本: {text_res}")
                
                client = AsyncOpenAI(
                    api_key="sk-swldhdfbzrwtesarrhxwbovcivpzezfshaxvcxrtwvdzylss",
                    base_url="https://api.siliconflow.cn/v1"
                )

                # 确保目录存在
                audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static/audio")
                os.makedirs(audio_dir, exist_ok=True)
                logging.info(f"确保音频目录存在: {audio_dir}")

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"speech_{timestamp}.mp3"
                relative_path = f"/static/audio/{filename}"
                absolute_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path.lstrip('/'))
                logging.info(f"准备生成语音文件: {absolute_path}")

                try:
                    logging.info("调用语音生成API")
                    async with client.audio.speech.with_streaming_response.create(
                        model=model_name,
                        voice=digital_human['video_path'],
                        #voice="FunAudioLLM/CosyVoice2-0.5B:alex",
                        input=text_res,
                        response_format="mp3"
                    ) as response:
                        async with aiofiles.open(absolute_path, "wb") as f:
                            async for chunk in response.iter_bytes():
                                await f.write(chunk)
                    logging.info(f"语音文件生成成功: {absolute_path}")
                except Exception as e:
                    logging.error(f"语音生成失败: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"语音生成失败: {str(e)}")

                if not os.path.exists(absolute_path):
                    logging.error(f"语音文件保存失败: {absolute_path}")
                    raise HTTPException(status_code=500, detail="语音文件保存失败")

                # 获取音频时长（使用mutagen库处理MP3文件）
                try:
                    from mutagen.mp3 import MP3
                    audio = MP3(absolute_path)
                    duration = audio.info.length
                    logging.info(f"音频时长: {duration}秒")
                except Exception as e:
                    logging.warning(f"无法获取音频时长: {str(e)}")
                    duration = 0  # 如果无法获取时长，设置为0

                # 5. 保存到数据库
                logging.info(f"保存音频到数据库: filename={filename}, filepath={relative_path}, digital_human_id={id}")
                result = db_manager.save_audio_to_database(
                    filename=filename,
                    filepath=relative_path,
                    digital_human_id=id,
                )
                
                if not result["success"]:
                    logging.error(f"音频保存到数据库失败: {result.get('error', '未知错误')}")
                
                response_data = {
                    "audio_url": relative_path,
                    "duration": duration
                }
                logging.info(f"生成音频成功，返回数据: {response_data}")
                logging.info("===== generate_audio 方法结束 =====")
                return response_data

        except HTTPException as e:
            logging.error(f"生成语音时发生HTTP错误: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"生成语音时发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"生成语音失败: {str(e)}")
    
    async def _read_local_file(self, file_path: str, max_size: int = 50 * 1024 * 1024) -> bytes:
        """从本地路径读取音频文件内容"""
        try:
            # 如果是URL，提取文件路径
            if file_path.startswith('http://') or file_path.startswith('https://'):
                # 从URL中提取文件路径
                if '/static/' in file_path:
                    # 提取/static/后面的部分
                    file_path = file_path.split('/static/')[-1]
                    logging.info(f"从URL提取的文件路径: {file_path}")
                else:
                    raise HTTPException(status_code=400, detail="无效的音频文件URL")
            
            # 构建完整的文件路径
            base_dir = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(base_dir, 'static', file_path.lstrip('/'))
            logging.info(f"尝试读取文件: {full_path}")
            
            # 检查文件是否存在
            if not os.path.isfile(full_path):
                # 尝试在audio目录下查找
                audio_path = os.path.join(base_dir, 'static', 'audio', os.path.basename(file_path))
                logging.info(f"尝试在audio目录下查找文件: {audio_path}")
                
                if os.path.isfile(audio_path):
                    full_path = audio_path
                else:
                    logging.error(f"文件不存在: {full_path} 或 {audio_path}")
                    raise HTTPException(status_code=404, detail=f"音频文件不存在: {os.path.basename(file_path)}")
            
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
                logging.info(f"成功读取文件: {full_path}, 大小: {len(content)} 字节")
                return content
        
        except HTTPException as e:
            raise e
        except Exception as e:
            logging.error(f"读取音频文件失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"读取音频文件失败: {str(e)}"
            )

    async def _download_audio_from_url(self, url: str, max_size: int = 50 * 1024 * 1024) -> bytes:
        """专用音频下载方法"""
        try:
            # 如果是本地URL，直接读取文件
            if url.startswith('http://localhost:') or url.startswith('https://localhost:'):
                # 从URL中提取文件路径
                file_path = url.split('/static/')[-1]
                # 构建完整的文件路径
                base_dir = os.path.dirname(os.path.dirname(__file__))
                full_path = os.path.join(base_dir, 'static', file_path)
                logging.info(f"尝试读取本地文件: {full_path}")
                
                # 检查文件是否存在
                if not os.path.exists(full_path):
                    # 尝试在audio目录下查找
                    alt_path = os.path.join(base_dir, 'static', 'audio', os.path.basename(file_path))
                    logging.info(f"尝试在audio目录下查找文件: {alt_path}")
                    if os.path.exists(alt_path):
                        full_path = alt_path
                    else:
                        logging.error(f"本地文件不存在: {full_path} 或 {alt_path}")
                        raise HTTPException(status_code=404, detail=f"本地文件不存在: {file_path}")

                # 读取文件
                async with aiofiles.open(full_path, 'rb') as f:
                    content = await f.read()
                    logging.info(f"成功读取本地文件: {full_path}, 大小: {len(content)} 字节")
                    return content

            # 如果是远程URL，使用httpx下载
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
            logging.error(f"HTTP下载失败: {e.response.status_code} {e.response.reason_phrase}")
            raise HTTPException(
                status_code=502,
                detail=f"无法下载音频文件: {e.response.status_code} {e.response.reason_phrase}"
            )
        except Exception as e:
            logging.error(f"下载音频文件失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"下载音频文件失败: {str(e)}"
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
