"""
数据库集成模块
处理所有与数据库相关的操作，为 Tkinter 应用程序提供简单的接口
"""

import os
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建 Flask 应用实例
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

# 初始化数据库
with app.app_context():
    db.create_all()
    if not User.query.first():
        default_user = User(username='admin', password='admin')
        db.session.add(default_user)
        db.session.commit()
        print("已创建默认用户: admin/admin")

def get_all_digital_humans():
    """获取所有数字人，转换为简单字典列表"""
    with app.app_context():
        digital_humans = DigitalHuman.query.all()
        return [
            {
                'id': dh.id,
                'name': dh.name,
                'phone': dh.phone,
                'description': dh.description,
                'user_id': dh.user_id
            }
            for dh in digital_humans
        ]

def get_digital_human(digital_human_id):
    """获取指定ID的数字人"""
    with app.app_context():
        digital_human = DigitalHuman.query.get(digital_human_id)
        if not digital_human:
            return None
        return {
            'id': digital_human.id,
            'name': digital_human.name,
            'phone': digital_human.phone,
            'description': digital_human.description,
            'user_id': digital_human.user_id
        }

def save_chat_to_database(chat_content, digital_human_id, filename=None):
    """保存聊天内容到数据库"""
    try:
        with app.app_context():
            # 获取数字人信息
            digital_human = DigitalHuman.query.get(digital_human_id)
            if not digital_human:
                return {'success': False, 'error': f"未找到ID为 {digital_human_id} 的数字人"}
            
            # 生成文件名（如果未提供）
            if not filename:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_history_{timestamp}.txt"
            
            # 保存文件到指定目录
            save_path = os.path.join(app.config['DIGITAL_HUMANS_DOCUMENTS'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(chat_content)

            # 创建文档记录
            document = Document(
                title=f"与{digital_human.name}的对话记录 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                filename=filename,
                filepath=f'digital_humans/documents/{filename}',
                file_type="txt",
                file_size=os.path.getsize(save_path),
                description=f"与数字人 {digital_human.name} 的对话记录",
                user_id=digital_human.user_id,
                digital_human_id=digital_human.id
            )
            db.session.add(document)
            db.session.commit()

            return {
                'success': True, 
                'digital_human_name': digital_human.name,
                'document_id': document.id
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def get_digital_human_documents(digital_human_id):
    """获取指定数字人的所有文档"""
    with app.app_context():
        documents = Document.query.filter_by(digital_human_id=digital_human_id).all()
        return [
            {
                'id': doc.id,
                'title': doc.title,
                'filename': doc.filename,
                'filepath': doc.filepath,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'upload_time': doc.upload_time,
                'description': doc.description
            }
            for doc in documents
        ]

def save_audio_to_database(filename, filepath, digital_human_id):
    """保存音频文件信息到数据库
    
    Args:
        filename (str): 音频文件名
        filepath (str): 相对文件路径
        digital_human_id (int): 数字人ID
        
    Returns:
        dict: 包含操作结果的字典
    """
    try:
        with app.app_context():
            # 获取数字人信息
            digital_human = DigitalHuman.query.get(digital_human_id)
            if not digital_human:
                return {'success': False, 'error': f"未找到ID为 {digital_human_id} 的数字人"}
            
            # 创建音频文件记录
            audio_file = AudioFile(
                filename=filename,
                filepath=filepath,
                digital_human_id=digital_human_id
            )
            db.session.add(audio_file)
            db.session.commit()

            return {
                'success': True,
                'audio_id': audio_file.id,
                'digital_human_name': digital_human.name
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)} 