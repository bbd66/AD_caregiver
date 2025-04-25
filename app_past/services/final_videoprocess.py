# 将选择的视频按固定长度分割，对每一 Part 压缩，并上传到 Gemini，生成分析结果，并根据生成的 json 时间线提取片段。
# 需配置 GOOGLE_API_KEY，SELECTED_MODEL，SEGMENT_DURATION，CHARACTER_IMAGE_PATH，CHARACTER_PROMPT，VIDEO_PROMPT，CLIP_TIME_BUFFER
# CLIP_TIME_BUFFER 的作用是在片段时长过短时，延长提取出的片段长度。

# -*- coding: utf-8 -*-

import os
import time
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog
import logging
from datetime import datetime
import re
import json
import subprocess
import math
from tkinter.filedialog import askopenfilename, askopenfilenames
from dotenv import load_dotenv
import threading
import ffmpeg
from tkinter.simpledialog import askstring
import pymysql
from tkinter import simpledialog, Toplevel, Text, Button, Label, Scrollbar, WORD, END

# 加载 .env 文件
load_dotenv()

# 配置API密钥
#GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
#if not GOOGLE_API_KEY:
#    raise ValueError("请在 .env 文件中设置 GOOGLE_API_KEY")

# 或直接输入GOOGLE_API_KEY
GOOGLE_API_KEY = 'AIzaSyAtFu4VazVTKeP4ltV-9sOeP8MdER77f78'  #输入你的Gemini API Key


# genai.configure(api_key=GOOGLE_API_KEY)
genai.configure(api_key= f"{GOOGLE_API_KEY}", transport="rest")

MODEL_CONFIG = {
    'gemini-1.5-pro': '专业版 - 适用于复杂任务',
    'gemini-1.5-flash': '快速版 - 适用于一般任务',
    'gemini-2.0-flash-exp': '实验版 - 新特性测试'
}
SELECTED_MODEL = 'gemini-1.5-flash'  # 默认选择快速版
# SELECTED_MODEL = 'gemini-1.5-pro'

SEGMENT_DURATION = 180  # 视频分段时长（秒）
ENABLE_COMPRESSION = True  # 是否启用视频压缩，默认为True
COMPRESSION_SIZE = 50  # 视频压缩大小，默认为50MB

# 使用Tkinter弹窗获取用户输入
def get_text_input(title, prompt, default_text="", width=80, height=15):
    """创建一个自定义对话框以获取多行文本输入"""
    result = []
    
    def on_ok():
        result.append(text.get("1.0", "end-1c"))
        dialog.destroy()
    
    def on_cancel():
        result.append(default_text)  # 如果取消，使用默认文本
        dialog.destroy()
    
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 创建对话框
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry(f"{width * 10}x{height * 20}")
    dialog.resizable(True, True)
    dialog.grab_set()  # 使对话框成为模态
    
    # 创建主容器
    main_frame = tk.Frame(dialog)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 添加提示标签
    label = tk.Label(main_frame, text=prompt, padx=10, pady=10)
    label.pack()
    
    # 创建文本框框架
    text_frame = tk.Frame(main_frame)
    text_frame.pack(fill="both", expand=True)
    
    # 添加文本框和滚动条
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
    text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text.yview)
    
    # 插入默认文本
    text.insert("1.0", default_text)
    
    # 添加按钮框架
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill="x", pady=(10, 0))
    
    # 添加按钮
    cancel_button = tk.Button(button_frame, text="取消", command=on_cancel, width=10)
    cancel_button.pack(side="right", padx=5)
    
    ok_button = tk.Button(button_frame, text="确定", command=on_ok, width=10)
    ok_button.pack(side="right", padx=5)
    
    # 居中显示窗口
    dialog.update_idletasks()
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x = (screen_width - dialog.winfo_width()) // 2
    y = (screen_height - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")
    
    # 确保所有组件都已正确显示
    dialog.update()
    
    # 等待用户操作
    dialog.wait_window()
    
    # 清理主窗口
    root.destroy()
    
    return result[0] if result else default_text

# 默认的角色提示词
DEFAULT_CHARACTER_PROMPT = """这个是你要分析的角色味芳，穿绿色毛衣的女士，你需要仔细记住她的人物特征，等下会基于此进行视频分析。
请注意她的特征：
1. 女性
2. 绿色毛衣
3. 中年女性
4. 短发
5. 表情通常较为严肃
6. 经常出现在室内场景

请记住这些特征，以便在视频中准确识别这个角色。当你在视频中看到与这些特征匹配的人物时，应标记为"味芳"。
请确保你能在视频的每一帧中都能识别出这个角色。"""

# 修改默认的视频分析提示词
DEFAULT_VIDEO_PROMPT = """你是一个专业的视频分析助手。请仔细分析视频中每一秒的画面，特别关注绿色毛衣的角色"味芳"的出现。

请按照以下要求进行分析：
1. 准确记录味芳出现的每个时间段
2. 详细描述她在每个时间段的表情、动作和行为
3. 使用"分:秒"格式标记时间（例如：1:05）
4. 确保描述的细节丰富且准确
5. 将分析结果以严格的JSON格式输出

输出格式示例：
{
    "Appearances": [
        {
            "clip": "clip_1",
            "start": "0:19",
            "end": "0:20",
            "description": "味芳出现在画面右侧，穿着绿色毛衣，表情严肃，正在翻阅文件。"
        }
    ]
}

请确保：
1. JSON格式完全正确，不包含任何额外字符
2. 时间格式统一为"分:秒"
3. 每个片段都有完整的描述
4. 不要输出任何其他格式的文本，只输出JSON

现在请开始分析视频并生成JSON格式的结果。"""

# 在程序开始时获取提示词
def get_prompts():
    # 获取角色分析提示词
    CHARACTER_PROMPT = get_text_input(
        "角色提示词",
        "请输入角色分析提示词（描述角色特征）:",
        DEFAULT_CHARACTER_PROMPT,
        width=100,
        height=20
    )
    
    # 获取视频分析提示词
    VIDEO_PROMPT = get_text_input(
        "视频分析提示词",
        "请输入视频分析提示词:",
        DEFAULT_VIDEO_PROMPT,
        width=100,
        height=20
    )
    
    return CHARACTER_PROMPT, VIDEO_PROMPT

CLIP_TIME_BUFFER = 2  # 视频片段前后的缓冲时间（秒）

# 确保log目录存在
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'batch_process.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置代理
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'

# 添加全局变量来控制暂停状态
is_paused = False
pause_event = threading.Event()

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',  # 数据库服务器地址
    'user': 'root',      # 数据库用户名
    'password': '12345678',  # 数据库密码
    'database': 'video_analysis',  # 数据库名
    'charset': 'utf8mb4'
}

def init_database():
    """初始化数据库和表结构"""
    try:
        # 连接MySQL数据库
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            
            # 创建视频处理记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_process_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    video_name VARCHAR(255) NOT NULL,
                    video_path TEXT NOT NULL,
                    process_start_time DATETIME NOT NULL,
                    process_end_time DATETIME,
                    status VARCHAR(50) NOT NULL,
                    total_parts INT,
                    processed_parts INT DEFAULT 0,
                    character_image_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建视频片段表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_segments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    video_record_id INT NOT NULL,
                    part_number INT NOT NULL,
                    segment_path TEXT NOT NULL,
                    start_time VARCHAR(20),
                    end_time VARCHAR(20),
                    duration INT,
                    status VARCHAR(50) NOT NULL,
                    analysis_result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_record_id) REFERENCES video_process_records(id)
                )
            """)
            
            # 创建分析结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    segment_id INT NOT NULL,
                    clip_number INT NOT NULL,
                    start_time VARCHAR(20) NOT NULL,
                    end_time VARCHAR(20) NOT NULL,
                    description TEXT,
                    extracted_clip_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (segment_id) REFERENCES video_segments(id)
                )
            """)
            
        connection.commit()
        logger.info("数据库初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return None

def create_video_record(video_path, character_image_path):
    """创建视频处理记录"""
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO video_process_records 
                (video_name, video_path, process_start_time, status, character_image_path)
                VALUES (%s, %s, %s, %s, %s)
            """
            video_name = os.path.basename(video_path)
            cursor.execute(sql, (
                video_name,
                video_path,
                datetime.now(),
                'STARTED',
                character_image_path
            ))
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"创建视频记录失败: {str(e)}")
        return None
    finally:
        if connection:
            connection.close()

def update_video_record(record_id, status, total_parts=None, processed_parts=None):
    """更新视频处理记录"""
    try:
        connection = get_db_connection()
        if not connection:
            return False
            
        with connection.cursor() as cursor:
            updates = []
            params = []
            
            if status:
                updates.append("status = %s")
                params.append(status)
            if total_parts is not None:
                updates.append("total_parts = %s")
                params.append(total_parts)
            if processed_parts is not None:
                updates.append("processed_parts = %s")
                params.append(processed_parts)
            if status == 'COMPLETED':
                updates.append("process_end_time = %s")
                params.append(datetime.now())
                
            if not updates:
                return True
                
            sql = f"UPDATE video_process_records SET {', '.join(updates)} WHERE id = %s"
            params.append(record_id)
            cursor.execute(sql, params)
            connection.commit()
            return True
    except Exception as e:
        logger.error(f"更新视频记录失败: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()

def create_segment_record(video_record_id, part_number, segment_path):
    """创建视频片段记录"""
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO video_segments 
                (video_record_id, part_number, segment_path, status)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (
                video_record_id,
                part_number,
                segment_path,
                'CREATED'
            ))
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"创建片段记录失败: {str(e)}")
        return None
    finally:
        if connection:
            connection.close()

def create_analysis_result(segment_id, clip_data):
    """创建分析结果记录"""
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO analysis_results 
                (segment_id, clip_number, start_time, end_time, description, extracted_clip_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                segment_id,
                clip_data['clip_number'],
                clip_data['start'],
                clip_data['end'],
                clip_data['description'],
                clip_data.get('extracted_clip_path', '')
            ))
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"创建分析结果记录失败: {str(e)}")
        return None
    finally:
        if connection:
            connection.close()

def compress_video_before_upload(input_file, target_size_mb):
    """在上传前压缩视频"""
    logger.info(f"开始压缩视频: {input_file}")
    logger.info(f"目标大小: {target_size_mb}MB")
    
    # 获取视频名称和基础名称
    video_name = os.path.splitext(os.path.basename(input_file))[0]
    base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
    
    # 创建输出目录结构
    output_dirs = {
        'main': os.path.join('outputs', base_name),
        'compressed': os.path.join('outputs', base_name, 'compressed')
    }

    # 创建所有必要的目录
    for dir_name, dir_path in output_dirs.items():
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"创建新的{dir_name}目录：{dir_path}")
        else:
            logger.info(f"使用已存在的{dir_name}目录：{dir_path}")

    # 生成压缩文件名
    filename = os.path.splitext(os.path.basename(input_file))[0]
    compressed_file = os.path.join(output_dirs['compressed'], f"{filename}_compressed.mp4")
    
    logger.info(f"压缩文件将保存至：{compressed_file}")
    
    # 获取视频时长
    
    try:
        # 获取视频时长
        cmd = ['ffmpeg', '-i', str(input_file)]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        _, stderr = process.communicate()
        
        duration = 0
        for line in stderr.split('\n'):
            if 'Duration' in line:
                time_str = line.split('Duration: ')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                duration = float(h) * 3600 + float(m) * 60 + float(s)
                break
        
        if duration == 0:
            logger.warning("无法获取视频时长，使用原始视频")
            return input_file
            
        # 计算目标比特率
        target_size_bits = target_size_mb * 8 * 1024 * 1024
        audio_bitrate = 128 * 1024  # 128kbps for audio
        video_bitrate = int((target_size_bits / duration) - audio_bitrate)
        
        if video_bitrate < 100 * 1024:
            logger.warning("计算出的视频比特率太低，使用最低比特率")
            video_bitrate = 100 * 1024
            
        logger.info(f"目标视频比特率：{video_bitrate/1024:.2f}k")
        
        # 压缩视频
        compress_cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264',    # 视频编码器
            '-b:v', f'{video_bitrate}',  # 视频比特率
            '-c:a', 'aac',     # 音频编码器
            '-b:a', '128k',     # 音频比特率
            '-preset', 'medium',   # 编码速度预设
            '-y',                  # 覆盖输出文件
            compressed_file
        ]
        
        logger.info("开始压缩...")
        process = subprocess.Popen(
            compress_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        process.communicate()
        
        if process.returncode == 0:
            original_size = os.path.getsize(input_file) / (1024 * 1024)
            compressed_size = os.path.getsize(compressed_file) / (1024 * 1024)
            logger.info(f"压缩完成！")
            logger.info(f"原始大小: {original_size:.2f}MB")
            logger.info(f"压缩后大小: {compressed_size:.2f}MB")
            logger.info(f"压缩率: {(1 - compressed_size/original_size) * 100:.2f}%")
            logger.info(f"压缩文件已保存: {compressed_file}")
            return compressed_file
        else:
            logger.error("压缩过程中出现错误，使用原始视频")
            return input_file
            
    except Exception as e:
        logger.error(f"压缩失败: {str(e)}，使用原始视频")
        return input_file

def get_video_files():
    """获取多个视频文件路径"""
    root = tk.Tk()
    root.withdraw()
    
    file_paths = filedialog.askopenfilenames(
        title='选择要分析的视频文件',
        filetypes=[('视频文件', '*.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gpp')]
    )
    
    if not file_paths:
        raise ValueError("未选择任何视频文件")
    
    return list(file_paths)

def upload_media_with_retry(file_path, media_type):
    """带重试机制的媒体文件上传"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"正在上传{media_type}... (尝试 {retry_count + 1}/{max_retries})")
            media_file = genai.upload_file(file_path)
            logger.info(f"上传完成: {media_file.uri}")
            return media_file
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                raise e
            logger.warning(f"上传失败，正在重试: {str(e)}")
            time.sleep(30)

def send_message_with_retry(chat, message, max_retries=5, retry_delay=30):
    """带重试机制的消息发送"""
    for attempt in range(max_retries):
        try:
            logger.info(f"[尝试 {attempt + 1}/{max_retries}] 开始发送消息...")
            response = chat.send_message(message, stream=False)
            logger.info(f"[尝试 {attempt + 1}/{max_retries}] 消息发送成功")
            return response
        except Exception as e:
            error_code = str(e).split()[0]  # 获取错误代码
            
            # 根据错误类型调整等待时间
            if error_code == "429":  # 配额限制
                wait_time = retry_delay * (attempt + 1)  # 递增等待时间
                logger.warning(f"达到API限制，等待 {wait_time} 秒后重试...")
            elif error_code == "500":  # 服务器错误
                wait_time = retry_delay * 2  # 服务器错误等待更长时间
                logger.warning(f"服务器暂时不可用，等待 {wait_time} 秒后重试...")
            else:
                wait_time = retry_delay
                logger.warning(f"发生错误: {str(e)}，等待 {wait_time} 秒后重试...")
            
            if attempt == max_retries - 1:  # 最后一次尝试
                logger.error(f"达到最大重试次数 ({max_retries})，放弃处理")
                raise e
                
            time.sleep(wait_time)
            continue

def time_to_seconds(time_str):
    """将 "分:秒" 格式转换为秒数"""
    try:
        if not time_str or ':' not in time_str:
            raise ValueError(f"无效的时间格式: {time_str}")
            
        parts = time_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"时间格式必须为 '分:秒': {time_str}")
            
        minutes = int(parts[0])
        seconds = float(parts[1])
        
        if minutes < 0 or seconds < 0 or seconds >= 60:
            raise ValueError(f"无效的时间值: {time_str}")
            
        return minutes * 60 + seconds
        
    except Exception as e:
        logger.error(f"时间转换错误: {str(e)}")
        return 0

def extract_clips(video_path, json_path, total_videos, current_index):
    """从视频中提取片段"""
    try:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
        part_match = re.search(r'Part(\d+)', video_name)
        
        if not part_match:
            logger.warning(f"[{current_index}/{total_videos}] 无法从文件名提取Part编号")
            return False
            
        part_number = part_match.group(1)
        
        # 创建提取结果目录
        extract_dir = os.path.join('outputs', base_name, 'extract')
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir, exist_ok=True)
            logger.info(f"创建新的提取输出目录：{extract_dir}")
        
        # 读取时间轴文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                timeline = json.load(f)
                logger.info(f"成功读取JSON文件：{json_path}")
                logger.debug(f"JSON内容：{json.dumps(timeline, ensure_ascii=False, indent=2)}")
        except Exception as e:
            logger.error(f"读取JSON文件失败：{str(e)}")
            return False
        
        if not timeline.get('Appearances'):
            logger.error(f"JSON文件中没有找到 Appearances 数组")
            return False
            
        # 遍历每个时间段并切割视频
        for i, clip in enumerate(timeline['Appearances'], 1):
            try:
                if not all(k in clip for k in ['start', 'end']):
                    logger.error(f"片段 {i} 缺少必要的时间信息")
                    continue
                    
                start_time = max(0, time_to_seconds(clip['start']) - CLIP_TIME_BUFFER)
                end_time = time_to_seconds(clip['end']) + CLIP_TIME_BUFFER
                duration = end_time - start_time
                
                if duration <= 0:
                    logger.error(f"片段 {i} 的时长无效：{duration}秒")
                    continue
                
                output_file = os.path.join(extract_dir, f'Part{part_number}_clip_{i}.mp4')
                
                logger.info(f'[{current_index}/{total_videos}] 正在处理片段 {i}: {clip["start"]} - {clip["end"]}')
                logger.info(f'开始时间: {start_time}秒, 结束时间: {end_time}秒, 时长: {duration}秒')
                
                try:
                    # 构建 ffmpeg 命令
                    command = [
                        'ffmpeg',
                        '-y',
                        '-i', video_path,
                        '-ss', str(start_time),
                        '-t', str(duration),
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        output_file
                    ]
                    
                    # 运行 ffmpeg 命令
                    logger.info(f'开始提取片段 {i}...')
                    
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    
                    # 设置超时时间（秒）
                    timeout = max(int(duration * 2), 30)  # 至少30秒
                    start_process_time = time.time()
                    
                    while process.poll() is None:
                        # 检查是否超时
                        if time.time() - start_process_time > timeout:
                            process.kill()
                            logger.error(f'片段 {i} 处理超时（{timeout}秒）')
                            break
                        
                        # 显示进度
                        elapsed = time.time() - start_process_time
                        logger.info(f'片段 {i} 处理中... 已用时：{int(elapsed)}秒')
                        time.sleep(2)  # 每2秒更新一次进度
                    
                    # 获取进程输出
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        logger.info(f'片段 {i} 提取成功：{output_file}')
                    else:
                        logger.error(f'片段 {i} 提取失败：{stderr}')
                        
                except Exception as e:
                    logger.error(f"运行 ffmpeg 命令时发生错误: {str(e)}")
                    continue
                    
            except Exception as e:
                logger.error(f"处理片段 {i} 时发生错误: {str(e)}")
                continue
        
        return True
        
    except Exception as e:
        logger.error(f"[{current_index}/{total_videos}] 提取片段时发生错误: {str(e)}")
        return False

def process_single_video(video_path, model, chat, image_file, total_videos, current_index, character_response, VIDEO_PROMPT, character_image_path, CHARACTER_PROMPT):
    """处理单个视频文件"""
    try:
        # 创建视频处理记录
        video_record_id = create_video_record(video_path, character_image_path)
        if not video_record_id:
            logger.error("创建视频处理记录失败")
            return False
            
        check_pause()  # 检查是否需要暂停
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        logger.info(f"=== 开始处理视频 [{current_index}/{total_videos}]: {video_name} ===")
        logger.info(f"视频路径: {video_path}")
        
        # 根据配置决定是否压缩视频
        if ENABLE_COMPRESSION:
            video_path_for_analysis = compress_video_before_upload(video_path, COMPRESSION_SIZE)
            logger.info(f"视频压缩已启用，使用压缩后的视频进行分析，压缩后大小为{COMPRESSION_SIZE}MB")
        else:
            video_path_for_analysis = video_path
            logger.info("视频压缩已禁用，使用原始视频进行分析")
        
        # 上传视频
        video_file = upload_media_with_retry(video_path_for_analysis, "视频")
        check_pause()  # 检查是否需要暂停
        
        # 等待视频处理
        logger.info("等待视频处理完成...")
        process_start_time = time.time()
        while video_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
            if time.time() - process_start_time > 300:  # 5分钟超时
                raise TimeoutError("视频处理超时")
        logger.info("视频处理已完成")
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"视频处理失败: {video_file.state.name}")
        
        # 发送第二轮问题
        check_pause()  # 检查是否需要暂停
        logger.info(f"[{current_index}/{total_videos}] 开始发送视频分析请求...")
        start_time = time.time()
        video_response = send_message_with_retry(chat, [VIDEO_PROMPT, video_file])
        end_time = time.time()
        response_time = end_time - start_time
        
        # 获取视频文件名
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        # 从文件名中提取基础名称（去掉Part和_compressedPart部分）
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)

        # 创建主文件夹和分析结果子文件夹
        main_folder = os.path.join('outputs', base_name)
        analysis_dir = os.path.join(main_folder, 'analysis')
        
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(analysis_dir):
            os.makedirs(analysis_dir, exist_ok=True)
            logger.info(f"创建新的分析输出目录：{analysis_dir}")
        else:
            logger.info(f"使用已存在的分析输出目录：{analysis_dir}")
        
        # 构建完整的输出文件路径
        output_file = os.path.join(analysis_dir, f"{video_name}_analysis.md")
        
        logger.info(f"[{current_index}/{total_videos}] 输出目录: {analysis_dir}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 视频分析会话 [{current_index}/{total_videos}]\n\n")
            f.write(f"## 基本信息\n")
            f.write(f"- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **视频**: {video_path}\n\n")            
            f.write(f"- **使用模型**: {SELECTED_MODEL}\n")
            
            # 获取相对路径
            relative_path = os.path.relpath(character_image_path, os.path.dirname(output_file))
            # 将Windows路径分隔符替换为正斜杠，并替换空格为%20
            safe_path = relative_path.replace('\\', '/').replace(' ', '%20')
            
            # 写入第一轮对话信息
            f.write("## 第一轮：角色特征分析\n\n")
            f.write(f"### 输入信息\n")
            f.write(f"- **图片**:\n\n![角色图片]({safe_path})\n\n")
            f.write(f"- **提示词**: {CHARACTER_PROMPT}\n\n")
            f.write("### 分析结果\n")
            f.write(f"{character_response.text}\n\n")
            f.write("### Token统计\n")
            f.write("| 类型 | 数量 |\n")
            f.write("|------|------|\n")
            f.write(f"| 输入Token | {character_response.usage_metadata.prompt_token_count} |\n")
            f.write(f"| 输出Token | {character_response.usage_metadata.candidates_token_count} |\n")
            f.write(f"| 总Token | {character_response.usage_metadata.total_token_count} |\n\n")
            
            # 写入第二轮对话信息
            f.write("## 第二轮：视频分析\n\n")
            f.write("### 输入信息\n")
            f.write(f"- **提示词**: {VIDEO_PROMPT}\n\n")
            f.write("### 分析结果\n")
            f.write(f"{video_response.text}\n\n")
            f.write("### Token统计\n")
            f.write("| 类型 | 数量 |\n")
            f.write("|------|------|\n")
            f.write(f"| 输入Token | {video_response.usage_metadata.prompt_token_count} |\n")
            f.write(f"| 输出Token | {video_response.usage_metadata.candidates_token_count} |\n")
            f.write(f"| 总Token | {video_response.usage_metadata.total_token_count} |\n")
            f.write(f"| 响应时间 | {response_time:.2f}秒 |\n\n")
            
            # 写入总体统计
            total_tokens = (character_response.usage_metadata.total_token_count + 
                           video_response.usage_metadata.total_token_count)
            f.write("## 总体统计\n\n")
            f.write("| 指标 | 数值 |\n")
            f.write("|------|------|\n")
            f.write(f"| 总Token消耗 | {total_tokens} |\n")
            f.write(f"| 总响应时间 | {response_time:.2f}秒 |\n")
        
        logger.info(f"[{current_index}/{total_videos}] 视频处理成功!")
        logger.info(f"处理时间: {response_time:.2f}秒")
        logger.info(f"结果已保存到: {output_file}")
        
        # 等待5秒后进行JSON调整
        logger.info(f"[{current_index}/{total_videos}] 等待5秒后进行JSON调整...")
        time.sleep(5)
        
        # 提取基础名称和Part编号
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
        part_match = re.search(r'Part(\d+)', video_name)
        
        if not part_match:
            logger.warning(f"[{current_index}/{total_videos}] 无法从文件名提取Part编号")
            return True
            
        part_number = part_match.group(1)
        
        # 构建JSON文件路径
        json_dir = os.path.join('outputs', base_name, 'splitjson')
        json_path = os.path.join(json_dir, f'Part{part_number}_{base_name}.json')
        
        if not os.path.exists(json_path):
            logger.warning(f"[{current_index}/{total_videos}] 未找到对应的JSON文件: {json_path}")
            return True
            
        try:
            # 读取txt文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            
            # 提取JSON内容
            analysis_json = extract_json_from_txt(txt_content)
            if not analysis_json:
                logger.error(f"[{current_index}/{total_videos}] 无法从分析结果中提取JSON内容")
                return True
            
            # 更新JSON内容
            analysis_json = update_json_content(analysis_json, part_number)
            
            # 读取原始JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                original_json = json.load(f)
            
            # 更新JSON内容
            original_json['Appearances'] = analysis_json['Appearances']
            
            # 保存更新后的JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(original_json, f, ensure_ascii=False, indent=4)
            
            logger.info(f"[{current_index}/{total_videos}] JSON更新成功: {json_path}")
            
        except Exception as e:
            logger.error(f"[{current_index}/{total_videos}] JSON处理失败: {str(e)}")
            return True
        
        # JSON处理完成后，等待5秒再开始提取视频片段
        logger.info(f"[{current_index}/{total_videos}] JSON处理完成，等待5秒后开始提取视频片段...")
        time.sleep(5)
        
        # 开始提取视频片段
        logger.info(f"[{current_index}/{total_videos}] 开始提取视频片段...")
        if extract_clips(video_path, json_path, total_videos, current_index):
            logger.info(f"[{current_index}/{total_videos}] 视频片段提取完成")
        else:
            logger.error(f"[{current_index}/{total_videos}] 视频片段提取失败")
        
        # 在处理完成后更新记录
        update_video_record(video_record_id, 'COMPLETED')
        
        return True
            
    except Exception as e:
        # 更新失败状态
        if 'video_record_id' in locals():
            update_video_record(video_record_id, 'FAILED')
        logger.error(f"处理视频失败: {str(e)}")
        return False

def split_video(input_file, segment_duration):
    """分割视频为指定时长的片段"""
    logger.info("=== 开始视频分割 ===")
    logger.info(f"输入文件: {input_file}")
    logger.info(f"分段时长: {segment_duration}秒")

    if not os.path.exists(input_file):
        logger.error(f"输入文件不存在: {input_file}")
        return False, []

    try:
        # 获取视频文件名和创建输出目录
        filename = os.path.basename(input_file)
        name, ext = os.path.splitext(filename)
        
        # 创建主文件夹结构
        main_folder = os.path.join('outputs', name)
        split_output_dir = os.path.join(main_folder, 'split')
        json_output_dir = os.path.join(main_folder, 'splitjson')
        
        # 创建所需目录
        for dir_path in [split_output_dir, json_output_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"创建新目录: {dir_path}")
            else:
                logger.info(f"使用已存在目录: {dir_path}")

        logger.info(f"视频输出目录: {split_output_dir}")
        logger.info(f"JSON输出目录: {json_output_dir}")
        
        # 设置FFmpeg命令
        output_pattern = os.path.join(split_output_dir, f'Part%d_{name}.mp4')
        
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-map', '0:v:0',
            '-map', '0:a:0?',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-f', 'segment',
            '-segment_time', str(segment_duration),
            '-reset_timestamps', '1',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            output_pattern
        ]
        
        logger.info("开始执行FFmpeg分割命令...")
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if process.returncode == 0:
            # 获取分割后的视频文件列表
            split_files = [os.path.join(split_output_dir, f) for f in os.listdir(split_output_dir) 
                         if f.startswith('Part') and f.endswith('.mp4') and name in f]
            
            # 为每个分割视频创建对应的JSON文件
            for video_file in split_files:
                video_name = os.path.splitext(os.path.basename(video_file))[0]
                json_name = f'{video_name}.json'
                json_path = os.path.join(json_output_dir, json_name)
                
                # 获取视频时长
                duration = get_video_info(video_file)
                
                # 创建JSON内容
                json_content = {
                    f"{video_name}_time": str(int(duration)),
                    "Appearances": []
                }
                
                # 写入JSON文件
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_content, f, ensure_ascii=False, indent=4)
                logger.info(f"创建JSON文件: {json_path}")
            
            logger.info(f"成功分割视频为 {len(split_files)} 个片段")
            return True, split_files
            
        else:
            logger.error(f"FFmpeg分割失败: {process.stderr}")
            return False, []
            
    except Exception as e:
        logger.error(f"视频分割过程中发生错误: {str(e)}")
        return False, []

def merge_json_files(json_files):
    """合并JSON文件"""
    if not json_files:
        logger.error("未选择JSON文件")
        return None, "请先选择JSON文件"
    
    try:
        # 获取原始文件名（从第一个文件名中提取）
        first_file = os.path.basename(json_files[0])
        base_name = re.sub(r'Part\d+_|\.json$', '', first_file)
        
        # 获取当前时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 构建新的输出文件名
        output_filename = f"{base_name}_all_{timestamp}.json"
        
        # 获取原始文件所在目录
        original_folder_path = os.path.dirname(json_files[0])
        
        # 构建输出路径
        output_path = os.path.join(original_folder_path, output_filename)
        
        # 修改排序逻辑
        try:
            # 按Part数字排序
            sorted_files = sorted(json_files, key=lambda x: int(re.search(r'Part(\d+)', x).group(1)))
        except (AttributeError, ValueError):
            # 如果无法按Part数字排序,就按文件名字母顺序排序
            sorted_files = sorted(json_files)
        
        merged_data = {
            "total_time": 0,
            "part_times": [],
            "Appearances": []
        }
        
        # 遍历所有JSON文件
        for json_file in sorted_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 获取完整的文件名（不含扩展名）
                full_part_name = os.path.splitext(os.path.basename(json_file))[0]
                
                # 使用完整的键名获取时间
                time_key = f"{full_part_name}_time"
                part_time = int(data.get(time_key, 0))
                
                merged_data["part_times"].append({
                    "part": full_part_name,
                    "time": part_time
                })
                merged_data["total_time"] += part_time
                
                # 直接添加 Appearances 数据
                for appearance in data.get("Appearances", []):
                    merged_data["Appearances"].append(appearance)
        
        # 保存合并后的文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
        return output_path, merged_data
        
    except Exception as e:
        logger.error(f"合并失败: {str(e)}")
        return None, None

def get_character_image():
    """获取角色图片路径"""
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title='选择角色图片',
        filetypes=[('图片文件', '*.png *.jpg *.jpeg *.bmp *.gif')],
        initialdir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input')
    )
    
    if not file_path:
        raise ValueError("未选择角色图片")
    
    # 创建input目录（如果不存在）
    input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input')
    os.makedirs(input_dir, exist_ok=True)
    
    return file_path

def batch_process():
    """批量处理视频"""
    # 初始化数据库
    if not init_database():
        logger.error("数据库初始化失败，程序退出")
        return
        
    # 启动暂停处理线程
    pause_thread = threading.Thread(target=pause_handler, daemon=True)
    pause_thread.start()
    
    start_time = time.time()
    logger.info("\n=== 7.videoprocess 开始 ===")
    logger.info("=== 批量视频处理启动 ===")
    logger.info("随时可以输入 pause 暂停程序，输入 continue 继续运行")
    
    try:
        # 获取角色图片
        logger.info("请选择角色图片...")
        character_image_path = get_character_image()
        logger.info(f"已选择角色图片: {character_image_path}")
        
        # 获取提示词
        CHARACTER_PROMPT, VIDEO_PROMPT = get_prompts()
        logger.info("已获取提示词")
        
        # 选择要分割的多个视频文件
        logger.info("请选择要处理的视频文件（可多选）...")
        input_files = askopenfilenames(
            title="选择要分割的视频文件（可多选）",
            filetypes=[("视频文件", "*.mp4;*.mkv;*.avi;*.mov;*.wmv")]
        )
        
        if not input_files:
            logger.error("未选择视频文件，程序退出")
            return
            
        # 将文件列表转换为列表并按名称排序
        input_files = sorted(list(input_files))
        logger.info(f"选择了 {len(input_files)} 个视频文件:")
        for idx, file_path in enumerate(input_files, 1):
            logger.info(f"  {idx}. {file_path}")
        
        # 分段时长使用配置值
        segment_duration = SEGMENT_DURATION
        logger.info(f"设定的分段时长: {segment_duration}秒")
        
        # 初始化总体统计
        total_successful = 0
        total_failed = 0
        
        # 初始化模型
        logger.info("正在初始化 Gemini 模型...")
        model = genai.GenerativeModel(SELECTED_MODEL)
        logger.info(f"当前使用模型: {SELECTED_MODEL}")
        logger.info(f"模型说明: {MODEL_CONFIG.get(SELECTED_MODEL, '未知模型')}")
        
        # 上传角色图片
        logger.info(f"上传角色示例图片: {character_image_path}")
        image_file = upload_image_with_retry(character_image_path)
        
        # 处理每个输入视频
        for file_idx, input_file in enumerate(input_files, 1):
            check_pause()  # 检查是否需要暂停
            video_basename = os.path.basename(input_file)
            logger.info(f"=== 处理视频文件 [{file_idx}/{len(input_files)}]: {video_basename} ===")
            logger.info(f"视频路径: {input_file}")
            
            # 执行视频分割
            success, split_files = split_video(input_file, segment_duration)
            if not success:
                logger.error(f"[{file_idx}/{len(input_files)}] 视频 {video_basename} 分割失败，跳过此视频")
                continue
            
            # 对分割后的视频文件按Part编号排序
            split_files.sort(key=lambda x: int(re.search(r'Part(\d+)', os.path.basename(x)).group(1)))
            logger.info(f"[{file_idx}/{len(input_files)}] 视频分割完成，共 {len(split_files)} 个片段")
            
            # 处理当前视频的所有片段
            for part_idx, video_path in enumerate(split_files, 1):
                check_pause()  # 检查是否需要暂停
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
                part_number = re.search(r'Part(\d+)', video_name).group(1)
                
                logger.info(f"=== 视频 [{file_idx}/{len(input_files)}] - Part {part_number} [{part_idx}/{len(split_files)}] ===")
                logger.info(f"视频名称: {video_name}")
                logger.info(f"基础名称: {base_name}")
                
                # 为每个视频创建新的会话
                chat = model.start_chat()
                
                # 角色分析
                logger.info(f"[视频 {file_idx}/{len(input_files)} - Part {part_number}] 发送角色分析请求...")
                character_response = send_message_with_retry(chat, [CHARACTER_PROMPT, image_file])
                logger.info(f"[视频 {file_idx}/{len(input_files)} - Part {part_number}] 角色特征分析完成")
                
                # 处理视频片段
                if process_single_video(video_path, model, chat, image_file, len(split_files), part_idx, character_response, VIDEO_PROMPT, character_image_path, CHARACTER_PROMPT):
                    check_pause()  # 检查是否需要暂停
                    total_successful += 1
                    logger.info(f"[视频 {file_idx}/{len(input_files)} - Part {part_number}] 处理成功")
                else:
                    total_failed += 1
                    logger.error(f"[视频 {file_idx}/{len(input_files)} - Part {part_number}] 处理失败")
                
                # 关闭当前会话
                logger.info(f"[{part_idx}/{split_files}] 关闭当前会话...")
                chat = None

                # 处理间隔
                if part_idx < len(split_files):
                    logger.info(f"[视频 {file_idx}/{len(input_files)} - Part {part_number}] 等待5秒后处理下一个片段...")
                    time.sleep(5)
            
            # 当前视频的所有片段处理完成，准备处理下一个视频
            if file_idx < len(input_files):
                logger.info(f"[{file_idx}/{len(input_files)}] {video_basename} 处理完成，等待5秒后处理下一个视频...")
                time.sleep(5)
        
        # 输出最终统计
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info("\n=== 批量处理完成 ===")
        logger.info(f"处理的视频文件数: {len(input_files)}")
        logger.info(f"处理的视频片段总数: {total_successful + total_failed}")
        logger.info(f"成功: {total_successful}")
        logger.info(f"失败: {total_failed}")
        logger.info(f"总耗时: {total_time:.2f}秒")
        logger.info(f"平均每个视频耗时: {total_time/len(input_files):.2f}秒")
        logger.info(f"平均每个片段耗时: {total_time/(total_successful + total_failed):.2f}秒")
        
        # 在处理完当前视频的所有片段后，执行JSON合并
        try:
            # 获取splitjson目录中的所有JSON文件
            json_dir = os.path.join('outputs', base_name, 'splitjson')
            json_files = [os.path.join(json_dir, f) for f in os.listdir(json_dir) 
                         if f.endswith('.json') and base_name in f]
            
            if json_files:
                logger.info(f"=== 开始合并JSON文件 [{file_idx}/{len(input_files)}] ===")
                output_path, merged_data = merge_json_files(json_files)
                
                if output_path and merged_data:
                    logger.info("JSON文件合并完成！")
                    logger.info(f"总时长：{merged_data['total_time']}秒")
                    logger.info(f"总片段数：{len(merged_data['Appearances'])}")
                    logger.info(f"输出文件：{output_path}")
                else:
                    logger.error("JSON合并失败")
        except Exception as e:
            logger.error(f"JSON合并过程中发生错误: {str(e)}")

        logger.info("=== 7.videoprocess 结束 ===")
        
    except Exception as e:
        # 计算处理时间
        end_time = time.time()
        total_time = end_time - start_time
        
        # 输出错误发生时的处理进度
        logger.error("\n=== 处理过程中发生错误 ===")
        logger.error(f"错误信息: {str(e)}")
        
        # 显示当前处理进度
        if 'file_idx' in locals() and 'input_files' in locals():
            current_video = os.path.basename(input_files[file_idx-1])
            logger.error(f"错误发生在第 {file_idx}/{len(input_files)} 个视频: {current_video}")
            
            if 'part_idx' in locals() and 'split_files' in locals():
                current_part = os.path.basename(split_files[part_idx-1])
                logger.error(f"错误发生在视频的第 {part_idx}/{len(split_files)} 个片段: {current_part}")
        
        # 输出已处理的统计信息
        logger.info("\n=== 处理中断时的统计 ===")
        logger.info(f"处理的视频文件数: {file_idx if 'file_idx' in locals() else 0}/{len(input_files)}")
        logger.info(f"处理的视频片段总数: {total_successful + total_failed}")
        logger.info(f"成功: {total_successful}")
        logger.info(f"失败: {total_failed}")
        logger.info(f"已用时: {total_time:.2f}秒")
        
        if total_successful + total_failed > 0:
            logger.info(f"平均每个片段耗时: {total_time/(total_successful + total_failed):.2f}秒")
        
        if 'file_idx' in locals():
            logger.info(f"平均每个视频耗时: {total_time/file_idx:.2f}秒")
        
        # 重新抛出异常
        raise

def extract_json_from_txt(txt_content):
    """从txt文件内容中提取JSON部分"""
    try:
        # 尝试多种可能的JSON格式
        patterns = [
            r'```json\s*({[\s\S]*?})\s*```',  # ```json {...} ```
            r'```\s*({[\s\S]*?})\s*```',      # ``` {...} ```
            r'{[\s\S]*"Appearances":\s*\[[\s\S]*?]}',  # 直接的JSON对象
            r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\})'  # 最通用的JSON对象匹配
        ]
        
        json_data = None
        for pattern in patterns:
            matches = re.finditer(pattern, txt_content)
            for match in matches:
                try:
                    # 获取JSON字符串
                    json_str = match.group(1) if pattern != r'{[\s\S]*"Appearances":\s*\[[\s\S]*?]}' else match.group(0)
                    
                    # 清理JSON字符串
                    json_str = json_str.strip()
                    # 删除注释行
                    json_str = re.sub(r'\s*//.*$', '', json_str, flags=re.MULTILINE)
                    # 删除多余的逗号
                    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                    
                    # 尝试解析JSON
                    potential_json = json.loads(json_str)
                    
                    # 验证是否包含必要的字段
                    if 'Appearances' in potential_json and isinstance(potential_json['Appearances'], list):
                        json_data = potential_json
                        logger.info("成功提取到JSON数据")
                        return json_data
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"JSON解析时发生错误: {str(e)}")
                    continue
        
        if json_data is None:
            # 如果没有找到有效的JSON，记录原始内容以便调试
            logger.error("[错误] 未找到有效的JSON数据")
            logger.debug("原始内容:")
            logger.debug(txt_content)
            return None
            
    except Exception as e:
        logger.error(f"[错误] 提取JSON时发生错误: {str(e)}")
        logger.debug("原始内容:")
        logger.debug(txt_content)
        return None

def update_json_content(json_data, part_number):
    """更新JSON内容，在每个Appearance中添加part信息并重新编号clip"""
    part_info = f'Part{part_number}'
    
    # 更新每个Appearance条目
    for i, appearance in enumerate(json_data['Appearances'], 1):
        # 创建新的有序字典，按照想要的顺序重新组织字段
        new_appearance = {
            'part': part_info,
            'clip': f'clip_{i}',
            'start': appearance['start'],
            'end': appearance['end'],
            'description': appearance['description']
        }
        # 用新的有序字典替换原来的条目
        json_data['Appearances'][i-1] = new_appearance
    
    return json_data

def get_video_info(video_path):
    """获取视频时长（秒）"""
    try:
        # 使用ffmpeg获取视频信息
        cmd = [
            'ffmpeg',
            '-i', video_path
        ]
        
        # 运行命令并捕获输出
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 在ffmpeg输出中查找持续时间信息
        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', result.stderr)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = int(duration_match.group(3))
            centiseconds = int(duration_match.group(4))
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
            return total_seconds
        else:
            raise ValueError("无法获取视频时长")
            
    except Exception as e:
        logger.error(f"获取视频信息失败: {str(e)}")
        return 0

def upload_image_with_retry(image_path):
    """带重试机制的图片文件上传"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"正在上传图片... (尝试 {retry_count + 1}/{max_retries})")
            image_file = genai.upload_file(image_path)
            logger.info(f"上传完成: {image_file.uri}")
            return image_file
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                raise e
            logger.warning(f"上传失败，正在重试: {str(e)}")
            time.sleep(30)

def check_pause():
    """检查是否需要暂停"""
    global is_paused
    while is_paused:
        pause_event.wait()  # 等待继续信号

def pause_handler():
    """处理暂停命令"""
    global is_paused
    while True:
        command = input().lower().strip()
        # 输入 pause 暂停程序，输入 continue 继续运行
        if command == 'pause':
            is_paused = True
            logger.info("程序已暂停，输入 continue 继续...")
        elif command == 'continue':
            is_paused = False
            pause_event.set()  # 发送继续信号
            pause_event.clear()  # 重置事件
            logger.info("程序继续运行...")

if __name__ == "__main__":
    batch_process()
