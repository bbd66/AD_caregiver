# 数字人护理助手 API

这是数字人护理助手应用的 FastAPI 后端。

## 项目结构

该项目遵循标准的 FastAPI 结构：

```
app/
├── api/                 # API 端点
│   ├── v1/              # API 版本 1
│   └── routes.py        # API 路由配置
├── core/                # 核心应用配置
│   └── config.py        # 设置和配置
├── db/                  # 数据库相关代码
│   ├── base/            # 模型基类
│   ├── crud/            # CRUD 操作
│   └── session/         # 数据库会话管理
├── dependencies/        # FastAPI 依赖项
│   └── auth.py          # 认证依赖项
├── middleware/          # 自定义中间件
│   └── logging.py       # 日志中间件
├── models/              # 数据库模型 (SQLAlchemy)
│   ├── digital_manage.py
│   ├── models_db.py
│   └── voice_deepseek_models.py
├── schemas/             # Pydantic 模式用于请求/响应验证
│   ├── deepseek.py
│   ├── digital_manage.py
│   └── voice.py
├── services/            # 业务逻辑
│   ├── deepseek.py
│   ├── digital_manage.py
│   ├── gemini_video_analysis.py
│   ├── voice.py
│   └── voice_deepseek.py
└── utils/               # 实用工具函数
    └── security.py      # 安全工具
├── main.py              # 主应用入口点
```

## 快速开始

1. 安装依赖项：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python main.py
```

3. 访问 API 文档：
```
http://localhost:8000/docs
```

## API 版本控制

API 使用版本控制以确保向后兼容性。所有端点都以 `/api/v1/...` 开头。

## 认证

API 使用 JWT bearer token 认证。要进行认证，请使用 `/api/v1/auth/token` 端点。 