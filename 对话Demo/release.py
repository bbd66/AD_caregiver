import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import json
import threading
import os
import datetime

API_KEY = "sk-7d54d72c0a314c45ae838b4ea422d152"
API_URL = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

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

    def get_response(self, user_input):
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a compassionate, patient, and understanding assistant focused on supporting and caring for individuals with Alzheimer's disease (AD). Your main goal is to enhance their quality of life by offering support, comfort, and practical help while respecting their dignity and autonomy. Interact with empathy and patience, using simple and clear communication. Provide gentle reminders and guidance for memory-related challenges. Address emotional needs with comfort and encouragement, always prioritizing safety and well-being. Promote cognitive and physical engagement through simple activities like reminiscence therapy, puzzles, or light exercises, and help maintain a stable daily routine. Support family members and caregivers by helping them understand the patient's needs and communicating effectively. Treat patients with respect and dignity, avoiding underestimation of their abilities. Adapt flexibly to changing needs and mood fluctuations, tailoring your approach to their current state.Please use Chinese language."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                response_data = response.json()
                reply = response_data["choices"][0]["message"]["content"]
                assistant_message = f"DeepSeek: {reply}\n"
                self.append_to_chat_history(assistant_message)
                self.save_to_file(assistant_message)
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
