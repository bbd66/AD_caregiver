import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext, messagebox
import requests
import json
import threading
import os
import datetime
from pathlib import Path
from openai import OpenAI
from playsound import playsound
import sounddevice as sd
import queue
import vosk
import numpy as np

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-7d54d72c0a314c45ae838b4ea422d152"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 语音合成 API 配置
TTS_API_KEY = "sk-swldhdfbzrwtesarrhxwbovcivpzezfshaxvcxrtwvdzylss"
TTS_BASE_URL = "https://api.siliconflow.cn/v1"

class voice：
    def upload_custom_voice(self, audio_file):
        """上传自定义音色到API"""
        try:
            voice_name = self.voice_name_entry.get().strip() # 这个可以用数字人的id
            
            with open(audio_file, "rb") as f:  # 读取MP3文件内容，即训练录音的文件
                audio_data = f.read()

            # 准备API参数
            url = "https://api.siliconflow.cn/v1/uploads/audio/voice" # 不要改动
            headers = {
                "Authorization": f"Bearer {TTS_API_KEY}"
            }
            files = {
                "file": ("temp_train_audio.wav", audio_data, "audio/wav")  
            }
            data = {
                "model": "FunAudioLLM/CosyVoice2-0.5B", # 训练用的模型
                "customName": voice_name, # 音色名字
                "text": "在一无所知中，梦里的一天结束了，一个新的轮回便会开始。"
            }

            # 发送请求
            response = requests.post(
                url,  
                headers=headers,
                files=files,
                data=data
            )

            if response.status_code == 200: # response.status_code 为 200 说明训练成功
                result = response.json()
                voice_uri = result['uri'] # 这里获取的uri字段相当于这个音色在模型里标识码，以后如果要使用这个音色，在生成音频时就要使用这个uri字段，因此建议作为数字人的信息存储


    def generate_speech(voice_uri, text):
        """生成音频文件"""
        try:
            #生成唯一文件名#
            # 获取当前时间戳（精确到秒）用于创建唯一文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # 构建完整文件路径（保存在当前脚本所在目录），也可以更改成别的
            speech_file = Path(__file__).parent / f"speech_{timestamp}.mp3"
            
            # 创建硅基流动API客户端实例
            client = OpenAI(
                api_key=TTS_API_KEY,     # 使用预定义的API密钥
                base_url=TTS_BASE_URL    # 指定语音合成服务端点
            )
            
            with client.audio.speech.with_streaming_response.create(
                model="FunAudioLLM/CosyVoice2-0.5B",
                voice=voice_uri,  # 使用当前选择的音色,即 upload_custom_voice 方法里得到的uri字段
                input=text,
                response_format="mp3"          # 指定模型输出音频的文件格式
            ) as response:
                response.stream_to_file(speech_file) # 生成的音频会存储到 speech_file 的路径下

# === DeepSeek 的代码，不是很了解所以不加注释了
    def get_response(self, user_input):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "（原有系统提示）"
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                response_data = response.json()
                reply = response_data["choices"][0]["message"]["content"]
                assistant_message = f"DeepSeek: {reply}\n"
                self.append_to_chat_history(assistant_message)
                self.save_to_file(assistant_message)
                # 启动语音生成线程
                threading.Thread(target=self.generate_speech, args=(reply,)).start()
            else:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                error_text = f"Error: {response.status_code} - {error_message}\n"
                self.append_to_chat_history(error_text, "error")
                self.append_to_chat_history("Please check your API key and network connection.\n", "error")
                self.save_to_file(error_text)
                self.save_to_file("Please check your API key and network connection.\n")
        except Exception as e:
            error_text = f"An error occurred: {str(e)}\n"
            self.append_to_chat_history(error_text, "error")
            self.append_to_chat_history("Please check your network connection and try again.\n", "error")
            self.save_to_file(error_text)
            self.save_to_file("Please check your network connection and try again.\n")

# vosk模型（录音识别为文字）
    def process_audio(self): # self 的类型是一个自定义的 Python 类（如 AudioTranscriber），该类封装了音频队列管理和 Vosk 模型调用逻辑。self 是一个实例对象
        """处理录音结果"""
        audio_data = b''.join(list(self.audio_queue.queue)) # 拼接所有音频数据
        
        if self.recognizer.AcceptWaveform(audio_data):      # 关键识别调用
            result = json.loads(self.recognizer.Result())   # 获取识别结果
            text = result.get('text', '')  # 提取文本内容，文件类型为txt



