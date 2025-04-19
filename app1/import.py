import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import json
import threading
import os
import datetime
from pathlib import Path
from openai import OpenAI
import pygame
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# 创建Flask应用实例（仅用于数据库访问）
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/app_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['DIGITAL_HUMANS_DOCUMENTS'] = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_humans', 'documents')
app.config['DIGITAL_HUMANS_BASE'] = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_humans', 'base')
app.config['DIGITAL_HUMANS_AUDIO'] = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_humans', 'audio')
db = SQLAlchemy(app)

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DIGITAL_HUMANS_DOCUMENTS'], exist_ok=True)
os.makedirs(app.config['DIGITAL_HUMANS_BASE'], exist_ok=True)
os.makedirs(app.config['DIGITAL_HUMANS_AUDIO'], exist_ok=True)

# 初始化pygame的音频系统
pygame.mixer.init()

# 数据库模型定义
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    digital_humans = db.relationship('DigitalHuman', backref='owner', lazy=True)

class DigitalHuman(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    description = db.Column(db.Text)
    reference_audio_path = db.Column(db.String(255))
    train_audio_path = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    video_path = db.Column(db.String(255))
    patient_info_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    upload_time = db.Column(db.DateTime, server_default=db.func.now())
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    digital_human_id = db.Column(db.Integer, db.ForeignKey('digital_human.id'))
    digital_human = db.relationship('DigitalHuman', backref='documents', lazy=True)

class AudioFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(255))
    upload_time = db.Column(db.DateTime, server_default=db.func.now())
    digital_human_id = db.Column(db.Integer, db.ForeignKey('digital_human.id'))
    digital_human = db.relationship('DigitalHuman', backref='audio_files', lazy=True)

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
        
        # 初始化数据库连接
        self.init_db()
        
        # 当前选中的数字人ID
        self.current_digital_human_id = None
        
        # 创建 UI 组件
        self.create_widgets()

        # 初始化聊天历史文件
        self.chat_history_file = None
        self.initialize_chat_file()
    
    def init_db(self):
        """初始化数据库连接"""
        try:
            with app.app_context():
                # 确保所有表已创建
                db.create_all()
                
                # 检查是否需要创建默认用户
                if not User.query.first():
                    default_user = User(username='admin', password='admin')
                    db.session.add(default_user)
                    db.session.commit()
                    print("已创建默认用户: admin/admin")
                print("数据库初始化成功")
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            messagebox.showerror("数据库错误", f"无法连接到数据库: {str(e)}\n\n应用程序将继续但数据库功能可能不可用")
            import traceback
            traceback.print_exc()
    
    def get_all_digital_humans(self):
        """获取所有数字人"""
        try:
            with app.app_context():
                return DigitalHuman.query.all()
        except Exception as e:
            print(f"获取数字人列表失败: {str(e)}")
            return []
    
    def get_user_digital_humans(self, user_id):
        """获取指定用户的所有数字人"""
        try:
            with app.app_context():
                return DigitalHuman.query.filter_by(user_id=user_id).all()
        except Exception as e:
            print(f"获取用户数字人失败: {str(e)}")
            return []
    
    def get_digital_human_documents(self, digital_human_id):
        """获取指定数字人的所有文档"""
        try:
            with app.app_context():
                return Document.query.filter_by(digital_human_id=digital_human_id).all()
        except Exception as e:
            print(f"获取数字人文档失败: {str(e)}")
            return []
    
    def get_digital_human_audio_files(self, digital_human_id):
        """获取指定数字人的所有音频文件"""
        try:
            with app.app_context():
                return AudioFile.query.filter_by(digital_human_id=digital_human_id).all()
        except Exception as e:
            print(f"获取数字人音频失败: {str(e)}")
            return []

    def create_widgets(self):
        # 顶部框架
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, padx=20, pady=5)

        # 标题
        title_label = tk.Label(
            top_frame, 
            text="DeepSeek Chat", 
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(side=tk.LEFT, pady=10)

        # 数字人选择框架
        dh_frame = tk.Frame(top_frame, bg="#f0f0f0")
        dh_frame.pack(side=tk.RIGHT, pady=10)

        # 数字人选择标签
        dh_label = tk.Label(
            dh_frame,
            text="选择数字人:",
            font=("Arial", 10),
            bg="#f0f0f0"
        )
        dh_label.pack(side=tk.LEFT, padx=5)

        # 数字人下拉菜单
        self.dh_var = tk.StringVar()
        self.dh_dropdown = tk.OptionMenu(dh_frame, self.dh_var, "")
        self.dh_dropdown.config(width=15)
        self.dh_dropdown.pack(side=tk.LEFT)
        
        # 更新数字人列表
        self.update_digital_humans_list()

        # 保存对话按钮
        save_button = tk.Button(
            dh_frame,
            text="保存对话",
            font=("Arial", 10),
            command=self.save_chat_as_document,
            bg="#2196F3",
            fg="white",
            padx=10
        )
        save_button.pack(side=tk.LEFT, padx=5)

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

    def initialize_chat_file(self):
        """初始化聊天历史文件，文件名包含时间戳"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_history_file = f"chat_history_{timestamp}.txt"

        if not os.path.exists(self.chat_history_file):
            with open(self.chat_history_file, "w", encoding="utf-8") as f:
                f.write(f"=== DeepSeek Chat History - {timestamp} ===\n\n")

    def update_digital_humans_list(self):
        """更新数字人下拉列表"""
        try:
            # 使用全局的app对象而非self的属性
            with app.app_context():
                digital_humans = DigitalHuman.query.all()
                
                # 清除现有选项
                menu = self.dh_dropdown["menu"]
                menu.delete(0, "end")
                
                # 添加"无"选项
                menu.add_command(
                    label="无",
                    command=lambda: self.dh_var.set("无")
                )
                
                # 添加数字人选项
                for dh in digital_humans:
                    # 创建一个局部变量，避免闭包问题
                    def create_command(d=dh):
                        return lambda: self.set_digital_human(d)
                    
                    menu.add_command(
                        label=f"{dh.name} (ID: {dh.id})",
                        command=create_command()
                    )
                
                # 默认选择"无"
                self.dh_var.set("无")
        except Exception as e:
            print(f"更新数字人列表出错: {str(e)}")
            messagebox.showerror("错误", f"获取数字人列表失败: {str(e)}")
    
    def set_digital_human(self, digital_human):
        """设置选中的数字人"""
        self.dh_var.set(f"{digital_human.name} (ID: {digital_human.id})")
        self.current_digital_human_id = digital_human.id

    def save_chat_as_document(self):
        """将当前对话保存为文档并关联到选中的数字人"""
        selected = self.dh_var.get()
        if selected == "无":
            messagebox.showwarning("警告", "请先选择一个数字人！")
            return

        try:
            # 从选项中提取数字人ID
            dh_id = int(selected.split("ID: ")[1].rstrip(")"))
            
            # 读取聊天历史内容
            if not self.chat_history_file or not os.path.exists(self.chat_history_file):
                messagebox.showerror("错误", "没有可保存的对话内容！")
                return

            with open(self.chat_history_file, "r", encoding="utf-8") as f:
                chat_content = f.read()

            # 使用全局的app对象的上下文
            with app.app_context():
                # 获取数字人信息
                digital_human = DigitalHuman.query.get(dh_id)
                if not digital_human:
                    messagebox.showerror("错误", "未找到选中的数字人！")
                    return
                
                # 生成文档文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_history_{timestamp}.txt"
                
                # 保存文件到指定目录
                save_path = os.path.join(app.config['DIGITAL_HUMANS_DOCUMENTS'], filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(chat_content)

                # 创建文档记录
                document = Document(
                    title=f"与{digital_human.name}的对话记录 - {timestamp}",
                    filename=filename,
                    filepath=f'digital_humans/documents/{filename}',
                    file_type="txt",
                    file_size=os.path.getsize(save_path),
                    description=f"与数字人 {digital_human.name} 的对话记录",
                    user_id=digital_human.user_id,
                    digital_human_id=dh_id
                )
                db.session.add(document)
                db.session.commit()

                messagebox.showinfo("成功", f"对话已成功保存到数据库并关联到数字人「{digital_human.name}」！")

        except Exception as e:
            messagebox.showerror("错误", f"保存文档时出错：{str(e)}")
            import traceback
            traceback.print_exc()

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
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            # 等待音频播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()