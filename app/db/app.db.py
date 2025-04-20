import pymysql
from typing import Dict, List, Optional, Tuple, Any
import os
import logging
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

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

# SQLAlchemy配置
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

class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='050729', 
                 db='app_db', port=3306, charset='utf8'):
        # 原生连接配置
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'db': db,
            'port': port,
            'charset': charset
        }
        self.connection = None
        self.cursor = None
        
        # SQLAlchemy引擎
        self.engine = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset={charset}", # 数据库连接URL
            pool_pre_ping=True
        )
        self.Session = sessionmaker(bind=self.engine)
        
    # 原生数据库操作方法（保持原有核心逻辑）
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = pymysql.connect(**self.connection_params)
            self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}", exc_info=True)
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = None
        self.connection = None
    
    def execute_query(self, query: str, params: Tuple = None) -> Optional[List[Dict]]:
        """执行查询并返回结果"""
        try:
            if not self.connection:
                self.connect()
            
            logger.info(f"执行SQL: {query}")
            self.cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Exception as e:
            logger.error(f"查询执行失败: {e}", exc_info=True)
            if self.connection:
                self.connection.rollback()
            return None

    # 增强版数字人管理方法（兼容新字段）
    def add_digital_human(self, digital_human_data: Dict[str, Any]) -> Optional[int]:
        """添加数字人记录（支持新字段）"""
        required_fields = {'name', 'user_id'}
        if not required_fields.issubset(digital_human_data.keys()):
            logger.error(f"缺少必填字段: {required_fields - digital_human_data.keys()}")
            return None

        field_mapping = {
            'avatar': 'image_path',
            'referenceAudio': 'reference_audio_path',
            'trainingAudio': 'train_audio_path',
            'videoPath': 'video_path',
            'patientInfoPath': 'patient_info_path'
        }

        valid_fields = [
            'name', 'phone', 'description', 'user_id',
            'reference_audio_path', 'train_audio_path', 
            'image_path', 'video_path', 'patient_info_path'
        ]

        insert_data = {}
        for key, value in digital_human_data.items():
            db_field = field_mapping.get(key, key)
            if db_field in valid_fields:
                insert_data[db_field] = value

        columns = ', '.join(insert_data.keys())
        placeholders = ', '.join(['%s'] * len(insert_data))
        query = f"INSERT INTO digital_human ({columns}) VALUES ({placeholders})"
        
        result = self.execute_query(query, tuple(insert_data.values()))
        if result is not None:
            return self.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
        return None

    # ORM扩展功能（新增文档和音频管理）
    def save_chat_record(self, chat_content: str, digital_human_id: int) -> Dict:
        """保存聊天记录（ORM实现）"""
        session = self.Session()
        try:
            dh = session.query(DigitalHuman).get(digital_human_id)
            if not dh:
                return {'success': False, 'error': '数字人不存在'}
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.txt"
            save_dir = os.path.join("static", "uploads", "documents")
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chat_content)
            
            doc = Document(
                title=f"与{dh.name}的对话记录",
                filename=filename,
                filepath=filepath,
                file_type="text/plain",
                file_size=os.path.getsize(filepath),
                digital_human_id=dh.id,
                user_id=dh.user_id
            )
            
            session.add(doc)
            session.commit()
            return {'success': True, 'document_id': doc.id}
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            session.close()

    # 数据库维护方法
    def check_tables_exist(self) -> bool:
        """检查所有表是否存在"""
        try:
            return all(self.engine.dialect.has_table(self.engine, t) 
                      for t in ['user', 'digital_human', 'document', 'audio_file'])
        except Exception as e:
            logger.error(f"表存在性检查失败: {e}")
            return False
            
    def create_all_tables(self) -> bool:
        """创建所有数据库表"""
        try:
            Base.metadata.create_all(self.engine)
            return True
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    db = DatabaseManager()
    
    # 初始化数据库
    if not db.check_tables_exist():
        if db.create_all_tables():
            logger.info("数据库表创建成功")
        else:
            logger.error("数据库表创建失败")
            exit(1)
    
    # 添加测试数字人
    new_dh = {
        'name': '测试数字人',
        'user_id': 1,
        'description': '集成测试用数字人',
        'referenceAudio': '/path/to/audio.wav',
        'videoPath': '/path/to/video.mp4'
    }
    dh_id = db.add_digital_human(new_dh)
    logger.info(f"创建数字人成功，ID: {dh_id}")
    
    # 保存聊天记录
    chat_result = db.save_chat_record("测试聊天内容", dh_id)
    if chat_result['success']:
        logger.info(f"保存聊天记录成功，文档ID: {chat_result['document_id']}")
    
    # 清理资源
    db.disconnect()
