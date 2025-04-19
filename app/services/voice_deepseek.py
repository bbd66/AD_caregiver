"""
数字人对话模拟系统
基于Tkinter的桌面应用，用于模拟与数字人的对话
"""
               
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import datetime
import json
import requests
import threading
import pygame
import db_integration
from PIL import Image, ImageTk
from pathlib import Path
from openai import OpenAI
import queue
import vosk
import sounddevice as sd
import numpy as np

# 默认用户配置
DEFAULT_USER_ID = 1  # 使用ID为1的用户

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-7d54d72c0a314c45ae838b4ea422d152"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 语音合成 API 配置
TTS_API_KEY = "sk-swldhdfbzrwtesarrhxwbovcivpzezfshaxvcxrtwvdzylss"
TTS_BASE_URL = "https://api.siliconflow.cn/v1"

# 初始化pygame的音频系统
pygame.mixer.init()

class DigitalHumanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("数字人对话模拟系统")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 12))
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TFrame", background="#f0f0f0")
        
        # 当前选择的数字人
        self.current_digital_human = None
        
        # 语音识别相关初始化
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.init_voice_recognition()
        
        # 音色相关初始化
        self.current_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
        self.custom_voices = {}
        self.load_voice_config()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧数字人列表框架
        self.left_frame = ttk.Frame(self.main_frame, width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 创建右侧聊天框架
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化界面组件
        self.init_left_panel()
        self.init_right_panel()
        
        # 加载数字人列表
        self.load_digital_humans()
    
    def init_left_panel(self):
        """初始化左侧面板"""
        # 标题
        title_label = ttk.Label(self.left_frame, text="数字人列表", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # 数字人列表框架
        list_frame = ttk.Frame(self.left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建树形视图
        columns = ("id", "name", "phone")
        self.dh_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # 定义列
        self.dh_tree.heading("id", text="ID")
        self.dh_tree.heading("name", text="姓名")
        self.dh_tree.heading("phone", text="电话")
        
        self.dh_tree.column("id", width=50)
        self.dh_tree.column("name", width=100)
        self.dh_tree.column("phone", width=120)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.dh_tree.yview)
        self.dh_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dh_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定选择事件
        self.dh_tree.bind("<<TreeviewSelect>>", self.on_dh_selected)
        
        # 按钮框架
        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 添加按钮
        refresh_btn = ttk.Button(btn_frame, text="刷新列表", command=self.load_digital_humans)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 文档管理按钮
        docs_btn = ttk.Button(btn_frame, text="文档管理", command=self.open_docs_window)
        docs_btn.pack(side=tk.RIGHT, padx=5)
    
    def init_right_panel(self):
        """初始化右侧面板"""
        # 聊天区域框架
        chat_frame = ttk.Frame(self.right_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 数字人信息
        self.info_frame = ttk.Frame(chat_frame)
        self.info_frame.pack(fill=tk.X, pady=5)
        
        self.dh_name_label = ttk.Label(self.info_frame, text="未选择数字人", font=("Arial", 14, "bold"))
        self.dh_name_label.pack(side=tk.LEFT, padx=5)
        
        self.dh_desc_label = ttk.Label(self.info_frame, text="")
        self.dh_desc_label.pack(side=tk.LEFT, padx=20)
        
        # 音色选择框架
        voice_frame = ttk.Frame(chat_frame)
        voice_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(voice_frame, text="音色选择:").pack(side=tk.LEFT, padx=5)
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
        train_btn = ttk.Button(
            voice_frame,
            text="训练音色",
            command=self.show_train_dialog
        )
        train_btn.pack(side=tk.RIGHT, padx=5)
        
        # 聊天历史
        chat_history_frame = ttk.LabelFrame(chat_frame, text="聊天历史")
        chat_history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_history = scrolledtext.ScrolledText(chat_history_frame, wrap=tk.WORD, font=("Arial", 11))
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_history.config(state=tk.DISABLED)
        
        # 输入区域
        input_frame = ttk.Frame(self.right_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.message_input = scrolledtext.ScrolledText(input_frame, height=4, font=("Arial", 11))
        self.message_input.pack(fill=tk.X, padx=5, pady=5)
        self.message_input.bind("<Return>", lambda e: self.send_message())
        
        # 按钮框架
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # 录音按钮
        self.record_button = ttk.Button(
            btn_frame,
            text="开始录音",
            command=self.start_stop_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(btn_frame, text="保存聊天", command=self.save_chat)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(btn_frame, text="清空聊天", command=self.clear_chat)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        send_btn = ttk.Button(btn_frame, text="发送", command=self.send_message)
        send_btn.pack(side=tk.RIGHT, padx=5)
    
    def init_voice_recognition(self):
        """初始化语音识别模型"""
        model_path = "vosk-model-small-cn-0.22"
        if not os.path.exists(model_path):
            messagebox.showerror("错误", "未找到语音模型文件，请先下载并解压模型文件到正确位置")
            return
            
        self.model = vosk.Model(model_path)
        self.samplerate = 16000
        self.recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
    
    def load_digital_humans(self):
        """加载数字人列表"""
        # 清空现有数据
        for item in self.dh_tree.get_children():
            self.dh_tree.delete(item)
        
        # 从数据库获取数字人列表
        digital_humans = db_integration.get_all_digital_humans()
        
        # 填充数据
        for dh in digital_humans:
            self.dh_tree.insert("", tk.END, values=(dh['id'], dh['name'], dh['phone']))
    
    def on_dh_selected(self, event):
        """数字人选择事件处理"""
        selected_items = self.dh_tree.selection()
        if not selected_items:
            return
            
        # 暂时解绑选择事件，防止重复选择
        self.dh_tree.unbind("<<TreeviewSelect>>")
        
        # 在后台线程中处理选择操作
        threading.Thread(target=self._handle_dh_selection, args=(selected_items[0],)).start()
    
    def _handle_dh_selection(self, selected_item):
        """在后台线程中处理数字人选择"""
        try:
            # 获取选中项的值
            values = self.dh_tree.item(selected_item, "values")
            dh_id = values[0]
            
            # 更新UI显示加载状态
            self.root.after(0, self._update_loading_state, True)
            
            # 获取数字人详细信息
            digital_human = db_integration.get_digital_human(dh_id)
            if not digital_human:
                self.root.after(0, messagebox.showerror, "错误", "无法获取数字人信息")
                return
            
            # 更新当前数字人
            self.current_digital_human = digital_human
            
            # 使用root.after更新UI
            self.root.after(0, self._update_ui_for_digital_human, digital_human)
            
            # 在后台发送系统提示
            self._send_system_prompt(digital_human)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "错误", f"选择数字人时发生错误: {str(e)}")
        finally:
            # 重新绑定选择事件
            self.root.after(0, lambda: self.dh_tree.bind("<<TreeviewSelect>>", self.on_dh_selected))
            # 关闭加载状态
            self.root.after(0, self._update_loading_state, False)
    
    def _update_loading_state(self, is_loading):
        """更新加载状态"""
        if is_loading:
            self.dh_name_label.config(text="正在加载数字人信息...")
            self.dh_desc_label.config(text="请稍候...")
            # 禁用按钮
            for child in self.right_frame.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(state="disabled")
        else:
            if not self.current_digital_human:
                self.dh_name_label.config(text="未选择数字人")
                self.dh_desc_label.config(text="")
            # 启用按钮
            for child in self.right_frame.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(state="normal")
    
    def _update_ui_for_digital_human(self, digital_human):
        """更新UI显示数字人信息"""
        # 更新标签
        self.dh_name_label.config(text=f"与 {digital_human['name']} 对话中")
        self.dh_desc_label.config(text="")
        
        # 清空聊天历史
        self.clear_chat()
    
    def _send_system_prompt(self, digital_human):
        """在后台发送系统提示"""
        try:
            # 构建系统提示，包含角色描述
            system_prompt = {
                "role": "system",
                "content": f"""你现在扮演的是一个名为{digital_human['name']}的数字人。

角色描述：
{digital_human['description']}

请注意：
1. 严格按照角色设定来回答问题
2. 保持专业、谨慎的态度"""
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [system_prompt],
                "stream": False
            }
            
            response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data))
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "未知错误")
                self.root.after(0, messagebox.showwarning, "警告", f"初始化数字人角色可能未成功: {error_message}")
        except Exception as e:
            self.root.after(0, messagebox.showwarning, "警告", f"初始化数字人角色时发生错误: {str(e)}")
    
    def send_message(self):
        """发送消息"""
        if not self.current_digital_human:
            messagebox.showwarning("警告", "请先选择一个数字人")
            return
        
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # 获取当前时间
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 添加用户消息到聊天历史
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, f"[{now}] 我: {message}\n\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
        
        # 清空输入框
        self.message_input.delete("1.0", tk.END)
        
        # 使用线程发送消息，避免阻塞 UI
        threading.Thread(target=self.get_ai_response, args=(message,)).start()
    
    def get_ai_response(self, user_input):
        """获取AI回复"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        # 构建消息历史，包含系统提示和用户输入
        messages = [
            {
                "role": "system",
                "content": f"""你现在扮演的是一个名为{self.current_digital_human['name']}的数字人。

角色描述：
{self.current_digital_human['description']}

请注意：
1. 严格按照角色设定来回答问题
2. 保持专业、谨慎的态度"""
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                response_data = response.json()
                reply = response_data["choices"][0]["message"]["content"]
                
                # 获取当前时间
                now = datetime.datetime.now().strftime("%H:%M:%S")
                
                # 添加AI回复到聊天历史
                self.chat_history.config(state=tk.NORMAL)
                self.chat_history.insert(tk.END, f"[{now}] {self.current_digital_human['name']}: {reply}\n\n")
                self.chat_history.see(tk.END)
                self.chat_history.config(state=tk.DISABLED)
                
                # 生成并播放语音
                threading.Thread(target=self.generate_speech, args=(reply,)).start()
            else:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "未知错误")
                messagebox.showerror("错误", f"获取AI回复失败: {error_message}")
        except Exception as e:
            messagebox.showerror("错误", f"获取AI回复时发生错误: {str(e)}")
    
    def generate_speech(self, text):
        """生成语音并播放"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"speech_{timestamp}.mp3"
            # 使用相对路径保存到static/uploads/digital_humans/audio目录
            relative_path = f"digital_humans/audio/{filename}"
            save_dir = os.path.join(os.path.dirname(__file__), "static", "uploads", "digital_humans", "audio")
            os.makedirs(save_dir, exist_ok=True)
            speech_file = os.path.join(save_dir, filename)
            
            client = OpenAI(
                api_key=TTS_API_KEY,
                base_url=TTS_BASE_URL
            )
            
            with client.audio.speech.with_streaming_response.create(
                model="FunAudioLLM/CosyVoice2-0.5B",
                voice=self.current_voice,  # 使用当前选择的音色
                input=text,
                response_format="mp3"
            ) as response:
                response.stream_to_file(speech_file)

            # 保存音频文件信息到数据库
            if self.current_digital_human:
                result = db_integration.save_audio_to_database(
                    filename=filename,
                    filepath=relative_path,
                    digital_human_id=self.current_digital_human['id']
                )
                if not result['success']:
                    print(f"音频保存到数据库失败: {result.get('error', '未知错误')}")

            # 播放音频
            self.play_audio(speech_file)
            
        except Exception as e:
            print(f"语音生成失败: {str(e)}")
    
    def play_audio(self, file_path):
        """播放音频文件"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            # 等待音频播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"音频播放失败: {str(e)}")
    
    def save_chat(self):
        """保存聊天记录"""
        if not self.current_digital_human:
            messagebox.showwarning("警告", "请先选择一个数字人")
            return
        
        chat_content = self.chat_history.get("1.0", tk.END)
        if not chat_content.strip():
            messagebox.showinfo("提示", "聊天内容为空，无需保存")
            return
        
        # 保存到数据库
        result = db_integration.save_chat_to_database(
            chat_content=chat_content,
            digital_human_id=self.current_digital_human['id']
        )
        
        if result['success']:
            messagebox.showinfo("成功", f"聊天记录已保存")
        else:
            messagebox.showerror("错误", f"保存失败: {result.get('error', '未知错误')}")
    
    def clear_chat(self):
        """清空聊天记录"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.config(state=tk.DISABLED)
    
    def open_docs_window(self):
        """打开文档管理窗口"""
        if not self.current_digital_human:
            messagebox.showwarning("警告", "请先选择一个数字人")
            return
        
        docs_window = tk.Toplevel(self.root)
        docs_window.title(f"{self.current_digital_human['name']} - 文档管理")
        docs_window.geometry("800x600")
        
        # 获取文档列表
        documents = db_integration.get_digital_human_documents(self.current_digital_human['id'])
        
        # 创建树形视图
        columns = ("id", "title", "file_type", "upload_time")
        docs_tree = ttk.Treeview(docs_window, columns=columns, show="headings", height=20)
        
        # 定义列
        docs_tree.heading("id", text="ID")
        docs_tree.heading("title", text="标题")
        docs_tree.heading("file_type", text="类型")
        docs_tree.heading("upload_time", text="上传时间")
        
        docs_tree.column("id", width=50)
        docs_tree.column("title", width=350)
        docs_tree.column("file_type", width=100)
        docs_tree.column("upload_time", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(docs_window, orient=tk.VERTICAL, command=docs_tree.yview)
        docs_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        docs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 填充数据
        for doc in documents:
            upload_time = doc['upload_time'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc['upload_time'], datetime.datetime) else str(doc['upload_time'])
            docs_tree.insert("", tk.END, values=(doc['id'], doc['title'], doc['file_type'], upload_time))

    def start_stop_recording(self):
        """开始/停止录音"""
        if not self.current_digital_human:
            messagebox.showwarning("警告", "请先选择一个数字人")
            return
            
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        self.record_button.configure(text="停止录音")
        self.audio_queue.queue.clear()
        threading.Thread(target=self.record_audio).start()

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        self.record_button.configure(text="开始录音")

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
                while self.is_recording:
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
                # 将识别结果填入输入框
                self.message_input.delete("1.0", tk.END)
                self.message_input.insert("1.0", text)
                # 自动发送消息
                self.send_message()

    def update_voice(self, event=None):
        """更新当前选择的音色"""
        selected = self.voice_combobox.get()
        if selected == "alex":
            self.current_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
        else:
            self.current_voice = self.custom_voices.get(selected, "alex")

    def show_train_dialog(self):
        """显示音色训练对话框"""
        if not self.current_digital_human:
            messagebox.showwarning("警告", "请先选择一个数字人")
            return
            
        train_dialog = tk.Toplevel(self.root)
        train_dialog.title("训练自定义音色")
        train_dialog.geometry("600x400")
        
        # 训练提示文本
        prompt_text = "请清晰朗读以下文本：\n\n在一无所知中，梦里的一天结束了，一个新的轮回便会开始。"
        ttk.Label(
            train_dialog,
            text=prompt_text,
            font=("Arial", 12),
            wraplength=550,
            justify=tk.LEFT
        ).pack(pady=20)
        
        # 音色名称输入
        name_frame = ttk.Frame(train_dialog)
        name_frame.pack(pady=10)
        ttk.Label(name_frame, text="音色名称:").pack(side=tk.LEFT)
        voice_name_entry = ttk.Entry(name_frame, width=30)
        voice_name_entry.pack(side=tk.LEFT, padx=5)
        
        # 录音控制按钮
        train_button = ttk.Button(
            train_dialog,
            text="开始训练录音",
            command=lambda: self.toggle_train_recording(train_dialog, train_button, voice_name_entry, status_label)
        )
        train_button.pack(pady=15)
        
        # 状态显示
        status_label = ttk.Label(train_dialog, text="")
        status_label.pack()
        
        # 初始化录音参数
        self.is_training = False
        self.train_audio = b''

    def toggle_train_recording(self, dialog, button, name_entry, status_label):
        """切换训练录音状态"""
        if not self.is_training:
            self.start_train_recording(dialog, button, status_label)
        else:
            self.stop_train_recording(dialog, button, name_entry, status_label)

    def start_train_recording(self, dialog, button, status_label):
        """开始训练录音"""
        self.is_training = True
        button.config(text="停止录音")
        status_label.config(text="录音中...请清晰朗读提示文本")
        
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

    def stop_train_recording(self, dialog, button, name_entry, status_label):
        """停止训练录音并上传"""
        self.is_training = False
        button.config(text="开始训练录音")
        status_label.config(text="处理中...请稍候")
        
        # 拼接音频数据
        audio_data = b''.join(list(self.train_queue.queue))
        
        # 保存为有效WAV文件
        temp_file = Path(__file__).parent / "temp_train_audio.wav"
        try:
            import wave
            with wave.open(str(temp_file), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)
        except Exception as e:
            status_label.config(text=f"保存音频失败：{str(e)}")
            return
        
        # 上传音色
        threading.Thread(
            target=self.upload_custom_voice,
            args=(temp_file, dialog, name_entry, status_label)
        ).start()

    def upload_custom_voice(self, audio_file, dialog, name_entry, status_label):
        """上传自定义音色到API"""
        try:
            # 获取用户输入
            voice_name = name_entry.get().strip()
            if not voice_name:
                status_label.config(text="错误：必须填写音色名称")
                return
            
            # 读取WAV文件内容
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            
            # 准备API参数
            url = "https://api.siliconflow.cn/v1/uploads/audio/voice"
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
            
            if response.status_code == 200:
                result = response.json()
                voice_uri = result['uri']
                
                # 更新本地记录
                self.custom_voices[voice_name] = voice_uri
                self.voice_combobox['values'] = ["alex"] + list(self.custom_voices.keys())
                self.save_voice_config()
                
                status_label.config(text="训练成功！现在可以使用自定义音色")
                dialog.after(2000, dialog.destroy)  # 2秒后关闭对话框
            else:
                error = response.json().get('error', '未知错误')
                status_label.config(text=f"训练失败：{error}")
                
        except Exception as e:
            status_label.config(text=f"请求错误：{str(e)}")
        finally:
            os.remove(audio_file)

    def save_voice_config(self):
        """保存音色配置到本地文件"""
        config_path = Path(__file__).parent / "voice_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.custom_voices, f)

    def load_voice_config(self):
        """加载本地音色配置"""
        config_path = Path(__file__).parent / "voice_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.custom_voices = json.load(f)

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalHumanApp(root)
    root.mainloop()
