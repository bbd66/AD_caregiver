import tkinter as tk
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

class DeepSeekChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek Chat")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # 创建 UI 组件
        self.create_widgets()

        # 初始化聊天历史文件
        self.chat_history_file = None
        self.initialize_chat_file()
         # Vosk语音识别初始化
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.init_voice_recognition()

    def init_voice_recognition(self):
        """初始化语音识别模型"""
        model_path = "vosk-model-small-cn-0.22"
        if not os.path.exists(model_path):
            messagebox.showerror("错误", "未找到语音模型文件")
            return
            
        self.model = vosk.Model(model_path)
        self.samplerate = 16000
        self.recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
        
    def create_widgets(self):
        # 标题
        title_label = tk.Label(
            self.root, 
            text="DeepSeek Chat", 
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=10)

        # 对话历史区域
        self.chat_history = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            width=90,
            height=25,
            font=("Arial", 12),
            bg="#ffffff"
        )
        self.chat_history.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.chat_history.config(state=tk.DISABLED)

        # 输入框
        input_frame = tk.Frame(self.root, bg="#f0f0f0")
        input_frame.pack(padx=20, pady=10, fill=tk.X)

        self.input_entry = tk.Entry(
            input_frame,
            font=("Arial", 12),
            width=70
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.send_message)

        # 发送按钮
        send_button = tk.Button(
            input_frame,
            text="Send",
            font=("Arial", 12),
            command=self.send_message,
            bg="#4CAF50",
            fg="white",
            padx=10
        )
        send_button.pack(side=tk.RIGHT, padx=5)

        # 退出按钮
        exit_button = tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 12),
            command=self.root.quit,
            bg="#f44336",
            fg="white",
            padx=10
        )
        exit_button.pack(pady=10)
        self.record_button = tk.Button(
            input_frame,
            text="开始录音",
            font=("Arial", 12),
            command=self.start_stop_recording,
            bg="#2196F3",
            fg="white",
            padx=10
        )
        self.record_button.pack(side=tk.RIGHT, padx=5)


    def initialize_chat_file(self):
        """初始化聊天历史文件，文件名包含时间戳"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_history_file = f"chat_history_{timestamp}.txt"

        if not os.path.exists(self.chat_history_file):
            with open(self.chat_history_file, "w", encoding="utf-8") as f:
                f.write(f"=== DeepSeek Chat History - {timestamp} ===\n\n")

    def send_message(self, event=None):
        user_input = self.input_entry.get().strip()
        if not user_input:
            return

        # 清空输入框
        self.input_entry.delete(0, tk.END)

        # 添加用户消息到对话历史
        user_message = f"You: {user_input}\n"
        self.append_to_chat_history(user_message, "user")
        self.save_to_file(user_message)

        # 使用线程发送消息，避免阻塞 UI
        threading.Thread(target=self.get_response, args=(user_input,)).start()

    def append_to_chat_history(self, text, role="assistant"):
        self.chat_history.config(state=tk.NORMAL)
        if role == "user":
            self.chat_history.insert(tk.END, text, "user")
            self.chat_history.tag_configure("user", foreground="blue")
        else:
            self.chat_history.insert(tk.END, text, "assistant")
            self.chat_history.tag_configure("assistant", foreground="black")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def save_to_file(self, text):
        """将对话内容保存到文件中"""
        try:
            if self.chat_history_file:
                with open(self.chat_history_file, "a", encoding="utf-8") as f:
                    f.write(text)
        except Exception as e:
            print(f"Error saving to file: {str(e)}")


    def generate_speech(self, text):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            speech_file = Path(__file__).parent / f"speech_{timestamp}.mp3"
            
            client = OpenAI(
                api_key=TTS_API_KEY,
                base_url=TTS_BASE_URL
            )
            
            with client.audio.speech.with_streaming_response.create(
                model="FunAudioLLM/CosyVoice2-0.5B",
                voice="FunAudioLLM/CosyVoice2-0.5B:alex",
                input=text,
                response_format="mp3"
            ) as response:
                response.stream_to_file(speech_file)

            # 在新线程中播放音频（避免阻塞UI）
            threading.Thread(
                target=self.play_audio, 
                args=(str(speech_file),),
                daemon=True
            ).start()
            
            #self.append_to_chat_history(f"语音已保存: {speech_file}\n", "system")  #这里注释掉可以让界面里不显示语音地址
        except Exception as e:
            error_msg = f"语音生成失败: {str(e)}\n"
            self.append_to_chat_history(error_msg, "error")

    def play_audio(self, file_path):
        try:
            playsound(file_path)
            # 播放完成后删除临时文件（可选）
            # os.remove(file_path)
        except Exception as e:
            error_msg = f"音频播放失败: {str(e)}\n"
            self.append_to_chat_history(error_msg, "error")

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


    def start_stop_recording(self):
        """开始/停止录音"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        self.record_button.config(text="停止录音", bg="#f44336")
        self.audio_queue.queue.clear()
        threading.Thread(target=self.record_audio).start()

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        self.record_button.config(text="开始录音", bg="#2196F3")

    def record_audio(self):
        """录音线程"""
        try:  # 修正此处缩进
            with sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            ):
             while self.is_recording:  # 循环保持录音状态
                sd.sleep(100)
            
            # 录音结束后处理结果
            self.process_audio()
            
        except Exception as e:
            messagebox.showerror("录音错误", str(e))

    def audio_callback(self, indata, frames, time, status):
        """音频采集回调"""
        if status:
            print(status)
        self.audio_queue.put(bytes(indata))

    def process_audio(self):
        """处理录音结果"""
        audio_data = b''.join(list(self.audio_queue.queue))
        
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            text = result.get('text', '')
            if text:
                # 将识别结果填入输入框并自动发送
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, text)
                self.send_message()

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()