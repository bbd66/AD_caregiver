import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20), unique=True)
    role = Column(Integer, nullable=False, default=0)  # 0=患者，1=管理员
    bound_to_user_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    digital_humans = relationship("DigitalHuman", backref="owner")
    bound_user = relationship("User", remote_side=[id], backref="bound_users")

class DigitalHuman(Base):
    """数字人模型"""
    __tablename__ = 'digital_human'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    phone = Column(String(20))
    description = Column(Text)
    reference_audio_path = Column(String(500))
    train_audio_path = Column(String(500))
    image_path = Column(String(500))
    video_path = Column(String(500))
    patient_info_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    documents = relationship("Document", back_populates="digital_human")
    audio_files = relationship("AudioFile", back_populates="digital_human")

class Document(Base):
    """文档模型"""
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    digital_human_id = Column(Integer, ForeignKey('digital_human.id'))
    digital_human = relationship("DigitalHuman", back_populates="documents")

class AudioFile(Base):
    """音频文件模型"""
    __tablename__ = 'audio_file'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255))
    filepath = Column(String(255))
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    digital_human_id = Column(Integer, ForeignKey('digital_human.id'))
    digital_human = relationship("DigitalHuman", back_populates="audio_files")
