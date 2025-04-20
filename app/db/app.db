"""
数据库集成模块
处理与数字人对话系统相关的所有数据库操作
使用SQLAlchemy ORM实现
"""

import os
import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session as DBSession

# 配置日志
logger = logging.getLogger("digital_human_db")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("db.log")
    ]
)

# 数据库配置
DATABASE_URL = "mysql+pymysql://root:Hh000412@localhost/app_db?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    description = Column(Text)
    reference_audio_path = Column(String(500))
    train_audio_path = Column(String(500))
    image_path = Column(String(500))
    video_path = Column(String(500))
    patient_info_path = Column(String(500))
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
Base.metadata.create_all(bind=engine)

class DatabaseManager:
    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def add_digital_human(self, digital_human_data: dict) -> Optional[int]:
        """添加数字人记录"""
        try:
            # 字段映射
            field_mapping = {
                'avatar': 'image_path',
                'referenceAudio': 'reference_audio_path',
                'trainingAudio': 'train_audio_path'
            }

            # 创建数字人对象
            dh = DigitalHuman(
                name=digital_human_data['name'],
                phone=digital_human_data.get('phone'),
                description=digital_human_data.get('description', ''),
                user_id=digital_human_data.get('user_id', 1)  # 示例用户ID
            )

            # 处理特殊字段
            for frontend_field, db_field in field_mapping.items():
                if frontend_field in digital_human_data:
                    setattr(dh, db_field, digital_human_data[frontend_field])

            self.session.add(dh)
            self.session.commit()
            return dh.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"添加数字人失败: {e}")
            return None

    def get_digital_human(self, dh_id: int) -> Optional[dict]:
        """获取单个数字人信息"""
        dh = self.session.query(DigitalHuman).get(dh_id)
        if not dh:
            return None
        
        return self._format_dh_response(dh)

    def get_all_digital_humans(self) -> List[dict]:
        """获取所有数字人列表"""
        try:
            digital_humans = self.session.query(DigitalHuman).all()
            return [self._format_dh_response(dh) for dh in digital_humans]
        except Exception as e:
            logger.error(f"获取数字人列表失败: {e}")
            return []

    def update_digital_human(self, dh_id: int, update_data: dict) -> bool:
        """更新数字人信息"""
        try:
            dh = self.session.query(DigitalHuman).get(dh_id)
            if not dh:
                return False

            field_mapping = {
                'avatar': 'image_path',
                'referenceAudio': 'reference_audio_path',
                'trainingAudio': 'train_audio_path'
            }

            for key, value in update_data.items():
                if key in ['name', 'phone', 'description']:
                    setattr(dh, key, value)
                elif key in field_mapping:
                    setattr(dh, field_mapping[key], value)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"更新数字人失败: {e}")
            return False

    def delete_digital_human(self, dh_id: int) -> bool:
        """删除数字人"""
        try:
            dh = self.session.query(DigitalHuman).get(dh_id)
            if not dh:
                return False

            self.session.delete(dh)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"删除数字人失败: {e}")
            return False

    def search_digital_humans(self, search_term: str, skip: int = 0, limit: int = 10) -> Tuple[List[dict], int]:
        """搜索数字人"""
        try:
            # 获取总数
            total = self.session.query(DigitalHuman).filter(
                or_(
                    DigitalHuman.name.ilike(f'%{search_term}%'),
                    DigitalHuman.phone.ilike(f'%{search_term}%'),
                    DigitalHuman.description.ilike(f'%{search_term}%')
                )
            ).count()

            # 获取分页结果
            results = self.session.query(DigitalHuman).filter(
                or_(
                    DigitalHuman.name.ilike(f'%{search_term}%'),
                    DigitalHuman.phone.ilike(f'%{search_term}%'),
                    DigitalHuman.description.ilike(f'%{search_term}%')
                )
            ).offset(skip).limit(limit).all()

            return [self._format_dh_response(dh) for dh in results], total
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return [], 0

    def _format_dh_response(self, dh: DigitalHuman) -> dict:
        """格式化数字人响应"""
        return {
            'id': dh.id,
            'name': dh.name,
            'phone': dh.phone,
            'description': dh.description,
            'avatar': dh.image_path,
            'referenceAudio': dh.reference_audio_path,
            'trainingAudio': dh.train_audio_path,
            'videoPath': dh.video_path,
            'patientInfoPath': dh.patient_info_path
        }

    def save_chat_history(self, dh_id: int, content: str) -> bool:
        """保存聊天记录"""
        try:
            dh = self.session.query(DigitalHuman).get(dh_id)
            if not dh:
                return False

            # 生成文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.txt"
            save_dir = os.path.join("static", "uploads", "documents")
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            doc = Document(
                title=f"与{dh.name}的对话记录",
                filename=filename,
                filepath=filepath,
                file_type="text/plain",
                file_size=os.path.getsize(filepath),
                digital_human_id=dh_id,
                user_id=dh.user_id
            )

            self.session.add(doc)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"保存聊天记录失败: {e}")
            return False

    def get_documents(self, dh_id: int) -> List[dict]:
        """获取文档列表"""
        try:
            docs = self.session.query(Document).filter_by(digital_human_id=dh_id).all()
            return [{
                'id': doc.id,
                'title': doc.title,
                'filename': doc.filename,
                'upload_time': doc.upload_time.isoformat()
            } for doc in docs]
        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return []

# 使用示例
if __name__ == "__main__":
    with DatabaseManager() as db:
        # 添加数字人
        new_dh = {
            'name': '测试数字人',
            'phone': '13800138000',
            'description': '整合测试',
            'avatar': '/path/to/avatar.jpg',
            'user_id': 1
        }
        dh_id = db.add_digital_human(new_dh)
        print(f"新增数字人ID: {dh_id}")

        # 查询数字人
        dh_info = db.get_digital_human(dh_id)
        print(f"数字人信息: {dh_info}")

        # 更新数字人
        update_result = db.update_digital_human(dh_id, {'description': '更新后的描述'})
        print(f"更新结果: {update_result}")

        # 保存聊天记录
        chat_result = db.save_chat_history(dh_id, "测试聊天内容")
        print(f"保存聊天记录: {chat_result}")

        # 获取文档列表
        docs = db.get_documents(dh_id)
        print(f"文档列表: {docs}")

        # 删除数字人
        delete_result = db.delete_digital_human(dh_id)
        print(f"删除结果: {delete_result}")
