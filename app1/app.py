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
        
        # 发送按钮
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        save_btn = ttk.Button(btn_frame, text="保存聊天", command=self.save_chat)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(btn_frame, text="清空聊天", command=self.clear_chat)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        send_btn = ttk.Button(btn_frame, text="发送", command=self.send_message)
        send_btn.pack(side=tk.RIGHT, padx=5)
    
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
        if selected_items:
            item = selected_items[0]
            values = self.dh_tree.item(item, "values")
            dh_id = values[0]
            
            # 获取数字人详细信息
            digital_human = db_integration.get_digital_human(dh_id)
            if digital_human:
                self.current_digital_human = digital_human
                self.dh_name_label.config(text=f"与 {digital_human['name']} 对话中")
                
                if digital_human['description']:
                    self.dh_desc_label.config(text=digital_human['description'])
                else:
                    self.dh_desc_label.config(text="暂无描述")
                
                # 清空聊天历史
                self.clear_chat()
    
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
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": f"你是一个名为{self.current_digital_human['name']}的数字人。请以这个身份进行对话。"
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
                voice="FunAudioLLM/CosyVoice2-0.5B:alex",
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalHumanApp(root)
    root.mainloop()
