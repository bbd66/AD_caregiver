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

class DeepSeekChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek Chat")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
                        
        self.current_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
        self.custom_voices = {}
        self.load_voice_config()

        # 创建音色选择组件
        self.create_voice_widgets()

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
        model_path = "vosk-model-small-cn-0.22"              # 这个是vosk模型的文件夹名，放在脚本的当前目录下
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
    
    def create_voice_widgets(self):
        """创建音色选择相关组件"""
        voice_frame = tk.Frame(self.root, bg="#f0f0f0")
        voice_frame.pack(pady=5, fill=tk.X, padx=20)

        # 音色选择标签
        tk.Label(
            voice_frame,
            text="音色选择:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT)

        # 音色下拉框
        self.voice_combobox = ttk.Combobox(
            voice_frame,
            values=["alex"] + list(self.custom_voices.keys()),
            state="readonly",
            width=25
        )
        self.voice_combobox.pack(side=tk.LEFT, padx=5)
        self.voice_combobox.current(0)
        self.voice_combobox.bind("<<ComboboxSelected>>", self.update_voice)

        # 训练音色按钮
        tk.Button(
            voice_frame,
            text="训练音色",
            command=self.show_train_dialog,
            font=("Arial", 12),
            bg="#9C27B0",
            fg="white"
        ).pack(side=tk.RIGHT)


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

    def update_voice(self, event=None):
        """更新当前选择的音色"""
        selected = self.voice_combobox.get()
        if selected == "alex":
            self.current_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
        else:
            self.current_voice = self.custom_voices.get(selected, "alex")

    def show_train_dialog(self):
        """显示音色训练对话框"""
        self.train_dialog = tk.Toplevel(self.root)
        self.train_dialog.title("训练自定义音色")
        self.train_dialog.geometry("600x400")

        # 训练提示文本
        prompt_text = "请清晰朗读以下文本：\n\n在一无所知中，梦里的一天结束了，一个新的轮回便会开始。"
        tk.Label(
            self.train_dialog,
            text=prompt_text,
            font=("Arial", 12),
            wraplength=550,
            justify=tk.LEFT
        ).pack(pady=20)

        # 音色名称输入
        name_frame = tk.Frame(self.train_dialog)
        name_frame.pack(pady=10)
        tk.Label(name_frame, text="音色名称:").pack(side=tk.LEFT)
        self.voice_name_entry = tk.Entry(name_frame, width=30)
        self.voice_name_entry.pack(side=tk.LEFT, padx=5)

        # 录音控制按钮
        self.train_button = tk.Button(
            self.train_dialog,
            text="开始训练录音",
            command=self.toggle_train_recording,
            font=("Arial", 12),
            bg="#E91E63",
            fg="white"
        )
        self.train_button.pack(pady=15)

        # 状态显示
        self.train_status = tk.Label(
            self.train_dialog,
            text="",
            fg="red"
        )
        self.train_status.pack()

        # 初始化录音参数
        self.is_training = False
        self.train_audio = b''
    
    def toggle_train_recording(self):
        """切换训练录音状态"""
        if not self.is_training:
            self.start_train_recording()
        else:
            self.stop_train_recording()

    def start_train_recording(self):
        """开始训练录音"""
        self.is_training = True
        self.train_button.config(
            text="停止录音",
            bg="#F44336"
        )
        self.train_status.config(text="录音中...请清晰朗读提示文本")
        
        # 初始化音频队列
        self.train_queue = queue.Queue()
        threading.Thread(target=self.capture_train_audio).start()

    def capture_train_audio(self):
        """捕获训练音频"""
        try:
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.train_audio_callback
            ):
                while self.is_training:
                    sd.sleep(100)
        except Exception as e:
            messagebox.showerror("录音错误", str(e))

    def train_audio_callback(self, indata, frames, time, status):
        """音频采集回调"""
        self.train_queue.put(bytes(indata))

    def stop_train_recording(self):
        """停止训练录音并上传"""
        self.is_training = False
        self.train_button.config(
            text="开始训练录音",
            bg="#E91E63"
        )
        self.train_status.config(text="处理中...请稍候")

        # =====下面是处理训练音频的程序===== #

        # 拼接音频数据
        audio_data = b''.join(list(self.train_queue.queue))
    
        # 保存为有效WAV文件
        temp_file = Path(__file__).parent / "temp_train_audio.wav"
        try:
            import wave
            with wave.open(str(temp_file), 'wb') as wf:
                wf.setnchannels(1)  # 单声道
                wf.setsampwidth(2)  # 16位PCM
                wf.setframerate(16000)  # 采样率16kHz
                wf.writeframes(audio_data)
        except Exception as e:
            self.train_status.config(text=f"保存音频失败：{str(e)}", fg="red")
            return

        # 上传音色
        threading.Thread(
            target=self.upload_custom_voice, # 这里是api的调用
            args=(temp_file,)
        ).start()
        # =====处理训练音频的程序到此结束===== #

    def upload_custom_voice(self, audio_file):
        """上传自定义音色到API"""
        try:
            # 获取用户输入
            voice_name = self.voice_name_entry.get().strip()
            if not voice_name:
                self.train_status.config(text="错误：必须填写音色名称")
                return

            # 读取MP3文件内容，即训练录音的文件
            with open(audio_file, "rb") as f:
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
                "model": "FunAudioLLM/CosyVoice2-0.5B",
                "customName": voice_name,
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
                voice_uri = result['uri']
                
                # 更新本地记录
                self.custom_voices[voice_name] = voice_uri
                self.voice_combobox['values'] = ["alex"] + list(self.custom_voices.keys())
                self.save_voice_config()
                
                self.train_status.config(
                    text="训练成功！现在可以使用自定义音色",
                    fg="green"
                )
            else:
                error = response.json().get('error', '未知错误')
                self.train_status.config(
                    text=f"训练失败：{error}",
                    fg="red"
                )
                
        except Exception as e:
            self.train_status.config(
                text=f"请求错误：{str(e)}",
                fg="red"
            )
        finally:
            os.remove(audio_file)

    def save_voice_config(self):
        """保存音色配置到本地文件"""
        config_path = Path(__file__).parent / "voice_config.json" # 用记事本打开 voice_config.json 就能看到各个音色的uri字段
        with open(config_path, 'w') as f:
            json.dump(self.custom_voices, f)

    def load_voice_config(self):
        """加载本地音色配置"""
        config_path = Path(__file__).parent / "voice_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.custom_voices = json.load(f)

    def generate_speech(self, text):
        try:
            #生成唯一文件名#
            # 获取当前时间戳（精确到秒）用于创建唯一文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # 构建完整文件路径（保存在当前脚本所在目录）
            speech_file = Path(__file__).parent / f"speech_{timestamp}.mp3"
            
            # 创建硅基流动API客户端实例
            client = OpenAI(
                api_key=TTS_API_KEY,     # 使用预定义的API密钥
                base_url=TTS_BASE_URL    # 指定语音合成服务端点
            )
            
            with client.audio.speech.with_streaming_response.create(
                model="FunAudioLLM/CosyVoice2-0.5B",
                voice=self.current_voice,  # 使用当前选择的音色,这里可以选择音色模型，alex是系统预置的音色，后面再增加用户训练音色功能
                input=text,
                response_format="mp3"          # 指定模型输出音频的文件格式
            ) as response:
                response.stream_to_file(speech_file)

            # 在新线程中播放音频（避免阻塞UI）
            threading.Thread(
                target=self.play_audio,        # 指定播放函数
                args=(str(speech_file),),      # 传递文件路径参数
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
        try:  
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
        self.audio_queue.put(bytes(indata))  # 将原始音频数据转为字节存入队列

    def process_audio(self):
        """处理录音结果"""
        audio_data = b''.join(list(self.audio_queue.queue)) # 拼接所有音频数据
        
        if self.recognizer.AcceptWaveform(audio_data):      # 关键识别调用
            result = json.loads(self.recognizer.Result())   # 获取识别结果
            text = result.get('text', '')  # 提取文本内容
            if text:
                # 将识别结果填入输入框并自动发送
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, text)
                self.send_message()

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()
