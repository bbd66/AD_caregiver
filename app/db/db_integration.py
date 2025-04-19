"""
数据库集成模块
处理与数字人对话系统相关的所有数据库操作
"""

import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 创建数据库引擎 - 使用 MySQL
DATABASE_URL = "mysql+pymysql://root:@localhost/app_db"
engine = create_engine(DATABASE_URL)

# 创建基类
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    digital_humans = relationship("DigitalHuman", backref="owner")

class DigitalHuman(Base):
    __tablename__ = 'digital_human'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    description = Column(Text)
    reference_audio_path = Column(String(255))
    train_audio_path = Column(String(255))
    image_path = Column(String(255))
    video_path = Column(String(255))
    patient_info_path = Column(String(255))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    documents = relationship("Document", back_populates="digital_human")
    audio_files = relationship("AudioFile", back_populates="digital_human")

class Document(Base):
    __tablename__ = 'document'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    filename = Column(String(255))
    filepath = Column(String(500))
    file_type = Column(String(50))
    file_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    digital_human_id = Column(Integer, ForeignKey('digital_human.id'))
    digital_human = relationship("DigitalHuman", back_populates="documents")

class AudioFile(Base):
    __tablename__ = 'audio_file'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(200), nullable=False)
    filepath = Column(String(500))
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    digital_human_id = Column(Integer, ForeignKey('digital_human.id'))
    digital_human = relationship("DigitalHuman", back_populates="audio_files")

# 创建所有表
Base.metadata.create_all(engine)

# 创建会话工厂
Session = sessionmaker(bind=engine)

def get_all_digital_humans():
    """获取所有数字人列表"""
    session = Session()
    try:
        digital_humans = session.query(DigitalHuman).all()
        return [{
            'id': dh.id, 
            'name': dh.name, 
            'phone': dh.phone,
            'description': dh.description,
            'reference_audio_path': dh.reference_audio_path,
            'train_audio_path': dh.train_audio_path,
            'image_path': dh.image_path,
            'video_path': dh.video_path,
            'patient_info_path': dh.patient_info_path,
            'user_id': dh.user_id
        } for dh in digital_humans]
    finally:
        session.close()

def get_digital_human(dh_id):
    """获取指定数字人的详细信息"""
    session = Session()
    try:
        dh = session.query(DigitalHuman).filter_by(id=dh_id).first()
        if dh:
            return {
                'id': dh.id,
                'name': dh.name,
                'phone': dh.phone,
                'description': dh.description,
                'reference_audio_path': dh.reference_audio_path,
                'train_audio_path': dh.train_audio_path,
                'image_path': dh.image_path,
                'video_path': dh.video_path,
                'patient_info_path': dh.patient_info_path,
                'user_id': dh.user_id
            }
        return None
    finally:
        session.close()

def save_chat_to_database(chat_content, digital_human_id):
    """保存聊天记录到数据库的 document 表"""
    session = Session()
    try:
        # 获取数字人信息
        digital_human = session.query(DigitalHuman).get(digital_human_id)
        if not digital_human:
            return {'success': False, 'error': f"未找到ID为 {digital_human_id} 的数字人"}
        
        # 生成文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.txt"
        
        # 保存文件到指定目录
        save_dir = os.path.join("static", "uploads", "digital_humans", "documents")
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(chat_content)
        
        # 创建文档记录
        document = Document(
            title=f"与{digital_human.name}的对话记录",
            filename=filename,
            filepath=f"digital_humans/documents/{filename}",
            file_type="txt",
            file_size=os.path.getsize(filepath),
            description=f"与数字人 {digital_human.name} 的对话记录",
            digital_human_id=digital_human.id,
            user_id=digital_human.user_id  # 使用数字人所属的用户ID
        )
        
        session.add(document)
        session.commit()
        return {'success': True}
    except Exception as e:
        session.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        session.close()

def get_digital_human_documents(digital_human_id):
    """获取指定数字人的文档列表"""
    session = Session()
    try:
        documents = session.query(Document).filter_by(digital_human_id=digital_human_id).all()
        return [{
            'id': doc.id,
            'title': doc.title,
            'file_type': doc.file_type,
            'upload_time': doc.upload_time
        } for doc in documents]
    finally:
        session.close()

def save_audio_to_database(filename, filepath, digital_human_id):
    """保存音频文件信息到数据库"""
    session = Session()
    try:
        audio = AudioFile(
            filename=filename,
            filepath=filepath,
            digital_human_id=digital_human_id
        )
        session.add(audio)
        session.commit()
        return {'success': True}
    except Exception as e:
        session.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        session.close() 