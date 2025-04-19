import pymysql
from typing import Dict, List, Optional, Tuple, Any
import os
import logging

# 配置日志
logger = logging.getLogger("digital_human_db")

class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='Hh000412', 
                 db='app_db', port=3306, charset='utf8'):
        """初始化数据库连接"""
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
            if params:
                logger.info(f"SQL参数: {params}")
            
            self.cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                results = self.cursor.fetchall()
                logger.info(f"查询结果: {results}")
                return results
            else:
                self.connection.commit()
                row_count = self.cursor.rowcount  # 获取受影响的行数
                logger.info(f"非查询SQL执行成功，受影响的行数: {row_count}")
                return row_count
        except Exception as e:
            logger.error(f"查询执行失败: {e}", exc_info=True)
            if self.connection:
                self.connection.rollback()
            return None
    
    def add_digital_human(self, digital_human_data: Dict[str, Any]) -> Optional[int]:
        """添加数字人记录
        
        Args:
            digital_human_data: 包含数字人信息的字典，字段包括:
                - name: 名字 (必填)
                - phone: 电话 (可选)
                - description: 描述 (可选)
                - referenceAudio: 参考音频的完整文件路径 (可选)
                - trainingAudio: 训练音频的完整文件路径 (可选)
                - avatar: 头像的完整文件路径 (可选)
                
        Returns:
            int: 新添加记录的ID，如果添加失败则返回None
        """
        logger.info(f"原始数据: {digital_human_data}")
        
        if 'name' not in digital_human_data or not digital_human_data['name']:
            logger.error("添加数字人失败: 名字字段必填")
            return None
        
        # 设置默认值，确保所有必要字段都存在
        if 'description' not in digital_human_data or not digital_human_data['description']:
            digital_human_data['description'] = f"{digital_human_data.get('name', '')} 的描述"
        
        # 处理字段名称映射
        field_mapping = {
            'avatar': 'image_path',
            'referenceAudio': 'reference_audio_path',
            'trainingAudio': 'train_audio_path'
        }
        
        # 记录特别关注的字段
        if 'avatar' in digital_human_data:
            logger.info(f"原始avatar字段值: {digital_human_data['avatar']}")
        if 'referenceAudio' in digital_human_data:
            logger.info(f"原始referenceAudio字段值: {digital_human_data['referenceAudio']}")
        if 'trainingAudio' in digital_human_data:
            logger.info(f"原始trainingAudio字段值: {digital_human_data['trainingAudio']}")
        
        # 创建一个新的字典，用于存储格式化后的数据
        formatted_data = {}
        
        # 复制原始数据，并进行字段名称映射
        for key, value in digital_human_data.items():
            # 如果存在映射关系，则使用映射后的字段名
            db_field = field_mapping.get(key, key)
            # 保留完整文件路径，不做任何修改
            formatted_data[db_field] = value
            logger.info(f"映射字段: {key} -> {db_field} = {value}")
        
        fields = []
        values = []
        params = []
        
        # 有效的数据库字段列表
        valid_fields = [
            'name', 'phone', 'description', 
            'reference_audio_path', 'train_audio_path', 'image_path'
        ]
        
        for field, value in formatted_data.items():
            if field in valid_fields:
                fields.append(field)
                values.append('%s')
                params.append(value)
                logger.info(f"添加数据库字段: {field} = {value}")
        
        if not fields:
            logger.error("添加数字人失败: 没有有效字段")
            return None
        
        query = f"INSERT INTO digital_human ({', '.join(fields)}) VALUES ({', '.join(values)})"
        logger.info(f"生成的SQL: {query}")
        logger.info(f"SQL参数: {params}")
        
        result = self.execute_query(query, tuple(params))
        if result is not None:
            # 获取最后插入的ID
            last_id = self.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
            logger.info(f"插入成功，获取到的ID: {last_id}")
            return last_id
        logger.error("插入失败，未能获取ID")
        return None
    
    def delete_digital_human(self, digital_human_id: int) -> bool:
        """删除数字人记录
        
        Args:
            digital_human_id: 要删除的数字人ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        query = "SELECT COUNT(*) as count FROM digital_human WHERE id = %s"
        result = self.execute_query(query, (digital_human_id,))
        if result is None or result[0]['count'] == 0:
            logger.warning(f"数据库中不存在ID为{digital_human_id}的数字人")
            return False
    
        query = "DELETE FROM digital_human WHERE id = %s"
        row_count = self.execute_query(query, (digital_human_id,))
        return row_count is not None and row_count > 0
    
    def get_digital_human(self, digital_human_id: int) -> Optional[Dict]:
        """根据ID获取数字人信息
        
        Args:
            digital_human_id: 数字人ID
            
        Returns:
            Dict: 包含数字人信息的字典，如果未找到则返回None
        """
        query = "SELECT * FROM digital_human WHERE id = %s"
        results = self.execute_query(query, (digital_human_id,))
        if results and len(results) > 0:
            logger.info(f"查询到的原始数据: {results[0]}")
            formatted = self._format_digital_human_response(results[0])
            logger.info(f"格式化后的数据: {formatted}")
            return formatted
        return None
    
    def _format_digital_human_response(self, db_record: Dict) -> Dict:
        """将数据库记录格式化为前端期望的响应格式
        
        Args:
            db_record: 数据库记录
            
        Returns:
            Dict: 格式化后的记录
        """
        # 字段名称映射（数据库字段 -> 前端字段）
        field_mapping = {
            'image_path': 'avatar',
            'reference_audio_path': 'referenceAudio',
            'train_audio_path': 'trainingAudio'
        }
        
        # 创建一个新的字典，用于存储格式化后的数据
        formatted_record = {}
        
        # 复制原始数据，并进行字段名称映射
        for key, value in db_record.items():
            # 如果存在映射关系，则使用映射后的字段名
            frontend_field = field_mapping.get(key, key)
            formatted_record[frontend_field] = value
            logger.info(f"映射响应字段: {key} -> {frontend_field} = {value}")
        
        # 确保所有必要字段都存在
        if 'description' not in formatted_record or not formatted_record['description']:
            formatted_record['description'] = f"{formatted_record.get('name', '')} 的描述"
            
        if 'referenceAudio' not in formatted_record or not formatted_record['referenceAudio']:
            formatted_record['referenceAudio'] = ''
            
        if 'trainingAudio' not in formatted_record or not formatted_record['trainingAudio']:
            formatted_record['trainingAudio'] = ''
            
        if 'avatar' not in formatted_record or not formatted_record['avatar']:
            formatted_record['avatar'] = ''
        
        return formatted_record
    
    def get_all_digital_humans(self) -> List[Dict]:
        """获取所有数字人记录
        
        Returns:
            List[Dict]: 包含所有数字人信息的列表
        """
        query = "SELECT * FROM digital_human ORDER BY id DESC"
        results = self.execute_query(query)
        return [self._format_digital_human_response(record) for record in results] if results else []
    
    def get_digital_humans_with_pagination(self, skip: int = 0, limit: int = 10) -> Tuple[List[Dict], int]:
        """获取数字人记录，支持分页
        
        Args:
            skip: 跳过的记录数
            limit: 每页记录数
            
        Returns:
            Tuple[List[Dict], int]: 包含分页结果和总记录数的元组
        """
        # 获取总记录数
        count_query = "SELECT COUNT(*) as total FROM digital_human"
        count_result = self.execute_query(count_query)
        total = count_result[0]['total'] if count_result else 0
        
        # 获取分页数据
        query = f"SELECT * FROM digital_human ORDER BY id DESC LIMIT {skip}, {limit}"
        results = self.execute_query(query)
        
        formatted_results = [self._format_digital_human_response(record) for record in results] if results else []
        return formatted_results, total
    
    def search_digital_humans(self, search_term: str, skip: int = 0, limit: int = 10) -> Tuple[List[Dict], int]:
        """搜索数字人记录
        
        Args:
            search_term: 搜索关键词
            skip: 跳过的记录数
            limit: 每页记录数
            
        Returns:
            Tuple[List[Dict], int]: 包含搜索结果和总记录数的元组
        """
        # 构建搜索条件
        search_condition = "%" + search_term + "%"
        
        # 获取匹配的总记录数
        count_query = """
            SELECT COUNT(*) as total 
            FROM digital_human 
            WHERE name LIKE %s 
               OR phone LIKE %s 
               OR description LIKE %s
        """
        count_params = (search_condition, search_condition, search_condition)
        count_result = self.execute_query(count_query, count_params)
        total = count_result[0]['total'] if count_result else 0
        
        # 获取分页搜索结果
        search_query = """
            SELECT * 
            FROM digital_human 
            WHERE name LIKE %s 
               OR phone LIKE %s 
               OR description LIKE %s
            ORDER BY id DESC
            LIMIT %s, %s
        """
        search_params = (search_condition, search_condition, search_condition, skip, limit)
        results = self.execute_query(search_query, search_params)
        
        formatted_results = [self._format_digital_human_response(record) for record in results] if results else []
        return formatted_results, total
    
    def update_digital_human(self, digital_human_id: int, update_data: Dict[str, Any]) -> bool:
        """更新数字人信息
        
        Args:
            digital_human_id: 要更新的数字人ID
            update_data: 包含要更新字段的字典
            
        Returns:
            bool: 更新成功返回True，否则返回False
        """
        if not update_data:
            logger.error("更新数字人失败: 没有提供更新数据")
            return False
        
        # 字段名称映射
        field_mapping = {
            'avatar': 'image_path',
            'referenceAudio': 'reference_audio_path',
            'trainingAudio': 'train_audio_path'
        }
        
        # 创建一个新的字典，用于存储格式化后的数据
        formatted_data = {}
        
        # 复制原始数据，并进行字段名称映射
        for key, value in update_data.items():
            # 如果存在映射关系，则使用映射后的字段名
            db_field = field_mapping.get(key, key)
            formatted_data[db_field] = value
        
        valid_fields = [
            'name', 'phone', 'description', 
            'reference_audio_path', 'train_audio_path', 'image_path'
        ]
        
        update_parts = []
        params = []
        
        for field, value in formatted_data.items():
            if field in valid_fields:
                update_parts.append(f"{field} = %s")
                params.append(value)
        
        if not update_parts:
            logger.error("更新数字人失败: 没有有效字段")
            return False
        
        params.append(digital_human_id)  # 添加ID参数
        
        query = f"UPDATE digital_human SET {', '.join(update_parts)} WHERE id = %s"
        result = self.execute_query(query, tuple(params))
        return result is not None

    def check_table_exists(self) -> bool:
        """检查digital_human表是否存在
        
        Returns:
            bool: 表存在返回True，否则返回False
        """
        query = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = 'digital_human'
        """
        result = self.execute_query(query, (self.connection_params['db'],))
        table_exists = result[0]['count'] > 0 if result else False
        logger.info(f"表是否存在: {table_exists}")
        return table_exists

    def create_table(self) -> bool:
        """创建digital_human表
        
        Returns:
            bool: 创建成功返回True，否则返回False
        """
        query = """
        CREATE TABLE IF NOT EXISTS digital_human (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            description TEXT,
            reference_audio_path VARCHAR(500),
            train_audio_path VARCHAR(500),
            image_path VARCHAR(500)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
        logger.info("创建表: digital_human")
        result = self.execute_query(query)
        logger.info(f"表创建结果: {result is not None}")
        return result is not None

    def add_missing_columns(self) -> bool:
        """添加可能缺失的列
        
        Returns:
            bool: 操作成功返回True，否则返回False
        """
        try:
            # 更新reference_audio_path、train_audio_path和image_path列的长度
            logger.info("检查并修改列长度")
            self._modify_column_length()
            return True
        except Exception as e:
            logger.error(f"添加列失败: {e}", exc_info=True)
            return False
    
    def _modify_column_length(self) -> bool:
        """修改文件路径列的长度，以适应完整的Windows路径
        
        Returns:
            bool: 操作成功返回True，否则返回False
        """
        try:
            # 先获取当前列信息
            column_info_query = """
                SELECT COLUMN_NAME, COLUMN_TYPE
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = 'digital_human'
                AND COLUMN_NAME IN ('reference_audio_path', 'train_audio_path', 'image_path')
            """
            column_info = self.execute_query(column_info_query, (self.connection_params['db'],))
            
            if column_info:
                for col in column_info:
                    col_name = col['COLUMN_NAME']
                    col_type = col['COLUMN_TYPE']
                    logger.info(f"当前列定义: {col_name} - {col_type}")
                    
                    # 如果长度不够500，进行修改
                    if 'varchar' in col_type.lower() and '500' not in col_type:
                        logger.info(f"修改列: {col_name} 的长度为VARCHAR(500)")
                        modify_query = f"""
                            ALTER TABLE digital_human 
                            MODIFY COLUMN {col_name} VARCHAR(500)
                        """
                        self.execute_query(modify_query)
            
            return True
        except Exception as e:
            logger.error(f"修改列长度失败: {e}", exc_info=True)
            return False


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("db.log")
        ]
    )
    
    db_manager = DatabaseManager(db='app_db')
    
    # 连接数据库
    if db_manager.connect():
        logger.info("数据库连接成功")
        
        # 确保表存在
        if not db_manager.check_table_exists():
            if db_manager.create_table():
                logger.info("成功创建digital_human表")
            else:
                logger.error("创建表失败")
                db_manager.disconnect()
                exit(1)
        else:
            # 如果表已存在，检查并添加可能缺失的列
            if db_manager.add_missing_columns():
                logger.info("检查并添加缺失列成功")
            else:
                logger.error("检查并添加缺失列失败")
        
        # 添加数字人示例
        new_digital_human = {
            'name': '数字人1',
            'phone': '13800138000',
            'description': '这是一个测试数字人',
            'referenceAudio': 'C:\\Users\\MSI-NB\\Desktop\\reference.wav',
            'trainingAudio': 'C:\\Users\\MSI-NB\\Desktop\\train.wav',
            'avatar': 'C:\\Users\\MSI-NB\\Desktop\\avatar.jpg'
        }
        
        new_id = db_manager.add_digital_human(new_digital_human)
        
        if new_id:
            logger.info(f"成功添加数字人，ID: {new_id}")
            
            # 查询示例
            digital_human = db_manager.get_digital_human(new_id)
            logger.info(f"查询到的数字人信息: {digital_human}")
            
            # 更新示例
            update_result = db_manager.update_digital_human(new_id, {'description': '更新后的描述'})
            logger.info(f"更新结果: {'成功' if update_result else '失败'}")
            
            # 分页示例
            page_results, total = db_manager.get_digital_humans_with_pagination(0, 10)
            logger.info(f"分页查询结果: 共{total}条记录，当前页{len(page_results)}条")
            
            # 搜索示例
            search_results, search_total = db_manager.search_digital_humans("数字人")
            logger.info(f"搜索结果: 共{search_total}条记录，当前页{len(search_results)}条")
            
            # 删除示例
            delete_result = db_manager.delete_digital_human(new_id)
            logger.info(f"删除结果: {'成功' if delete_result else '失败'}")
        
        # 断开连接
        db_manager.disconnect()
    else:
        logger.error("数据库连接失败")