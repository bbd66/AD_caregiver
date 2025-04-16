from sqlalchemy import Column, String, Boolean, Text, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


# class Avatar(Base):
#     """虚拟形象模型"""
#     __tablename__ = "avatars"
    
#     id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
#     name = Column(String, nullable=False)
#     type = Column(String, nullable=False)  # realistic, cartoon, anime, stylized
#     description = Column(Text, nullable=True)
#     features = Column(JSON, nullable=True)  # 存储虚拟形象特征的JSON
#     preview_url = Column(String, nullable=False)
#     model_url = Column(String, nullable=True)  # 3D模型URL
#     thumbnail_url = Column(String, nullable=False)
#     voice_id = Column(String, ForeignKey("voices.id"), nullable=True)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, server_default=func.now())
#     updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# class AvatarTemplate(Base):
#     """虚拟形象模板模型"""
#     __tablename__ = "avatar_templates"
    
#     id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
#     name = Column(String, nullable=False)
#     type = Column(String, nullable=False)  # realistic, cartoon, anime, stylized
#     description = Column(Text, nullable=False)
#     preview_url = Column(String, nullable=False)
#     thumbnail_url = Column(String, nullable=False)
#     features = Column(JSON, nullable=True)  # 默认特征的JSON
#     created_at = Column(DateTime, server_default=func.now())
#     updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

