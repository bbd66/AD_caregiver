# 数字人管理系统

这是一个用于管理数字人的后端API系统，基于FastAPI构建。该系统提供了数字人的增删查功能，可与前端应用集成实现完整的数字人管理。

## 功能特点

- 数字人的创建、查询和删除
- 支持分页和关键词搜索
- RESTful API设计
- 交互式API文档（由FastAPI提供）

## 环境要求

- Python 3.7+
- MySQL 5.7+
- PyMySQL
- FastAPI
- Uvicorn

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn pymysql
```

### 2. 配置数据库

在 `db.py` 文件中修改数据库连接参数：

```python
self.connection_params = {
    'host': 'localhost',  # 数据库主机地址
    'user': 'root',       # 数据库用户名
    'password': 'Hh000412', # 数据库密码
    'db': 'app_db',       # 数据库名
    'port': 3306,         # 数据库端口
    'charset': 'utf8'     # 字符集
}
```

### 3. 启动服务

```bash
python main.py
```

服务将在 http://localhost:8000 运行，API文档可在 http://localhost:8000/docs 访问。

## API接口

### 1. 创建数字人

- **URL**: `/digital-humans/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "name": "数字人姓名",
    "phone": "联系电话",
    "description": "描述信息",
    "reference_audio_path": "参考音频路径",
    "train_audio_path": "训练音频路径",
    "image_path": "图片路径"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "创建数字人成功",
    "data": {
      "id": 1,
      "name": "数字人姓名",
      "phone": "联系电话",
      "description": "描述信息",
      "reference_audio_path": "参考音频路径",
      "train_audio_path": "训练音频路径",
      "image_path": "图片路径"
    }
  }
  ```

### 2. 获取数字人列表

- **URL**: `/digital-humans/`
- **方法**: `GET`
- **查询参数**:
  - `skip`: 分页起始位置（默认0）
  - `limit`: 每页数量（默认10）
  - `search`: 搜索关键词（可选）
- **响应**:
  ```json
  {
    "success": true,
    "message": "获取数字人列表成功",
    "data": {
      "items": [
        {
          "id": 1,
          "name": "数字人1",
          "phone": "13800138000",
          "description": "描述信息",
          "reference_audio_path": "/path/to/audio.wav",
          "train_audio_path": "/path/to/train.wav",
          "image_path": "/path/to/image.jpg"
        }
      ],
      "total": 1
    }
  }
  ```

### 3. 获取单个数字人

- **URL**: `/digital-humans/{digital_human_id}`
- **方法**: `GET`
- **响应**:
  ```json
  {
    "success": true,
    "message": "获取数字人成功",
    "data": {
      "id": 1,
      "name": "数字人1",
      "phone": "13800138000",
      "description": "描述信息",
      "reference_audio_path": "/path/to/audio.wav",
      "train_audio_path": "/path/to/train.wav",
      "image_path": "/path/to/image.jpg"
    }
  }
  ```

### 4. 删除数字人

- **URL**: `/digital-humans/{digital_human_id}`
- **方法**: `DELETE`
- **响应**:
  ```json
  {
    "success": true,
    "message": "成功删除ID为1的数字人"
  }
  ```

## 前后端集成

前端可以通过这些API接口与后端进行交互，实现数字人的管理功能：

1. 调用创建API添加新数字人
2. 获取数字人列表展示在页面上
3. 点击列表项获取单个数字人详情
4. 删除不需要的数字人

## 注意事项

- 请确保MySQL服务已正确配置并运行
- 在生产环境中，应该对CORS进行适当配置，限制允许访问的域名
- 对于文件路径字段，本系统只存储路径，不负责文件上传和存储 