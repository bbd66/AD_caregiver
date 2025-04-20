import os
import json
from pathlib import Path
import datetime

class Database:
    def __init__(self):
        self.chat_history_file = None
        self.initialize_chat_file()

    def initialize_chat_file(self):
        """初始化聊天历史文件"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_history_file = f"chat_history_{timestamp}.txt"

        if not os.path.exists(self.chat_history_file):
            with open(self.chat_history_file, "w", encoding="utf-8") as f:
                f.write(f"=== DeepSeek Chat History - {timestamp} ===\n\n")

    def save_message(self, text):
        """保存消息到文件"""
        try:
            if self.chat_history_file:
                with open(self.chat_history_file, "a", encoding="utf-8") as f:
                    f.write(text)
        except Exception as e:
            raise Exception(f"保存文件失败: {str(e)}")
