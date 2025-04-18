# 数字虚拟人系统后端

基于FastAPI的数字虚拟人系统后端，包含虚拟形象构建、语音识别和数据管理功能。

## 功能特性

- **虚拟形象构建**：基于模板或自定义参数构建3D虚拟形象
- **语音识别**：语音输入识别和转换


## 目录结构

```
digital-human/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── voice.py             # 语音识别API
│   │   │   ├── avatar_builder.py    # 虚拟形象构建API
│   │   │   ├── dialogue.py          # 对话引擎API
|   |   |   └── digital_human.py     # 数字人管理API
│   │   └── routes.py                # API路由注册
│   ├── core/
│   │   └── config.py                # 应用配置
│   ├── db/
│   │   ├── base_class.py            # 数据库基类
│   │   ├── session.py               # 数据库会话
│   │   ├── models.py                # 数据库模型
│   │   └── init_db.py               # 数据库初始化
│   ├── models/
│   │   ├── voice.py                 # 语音模型
│   │   └── avatar_builder.py        # 虚拟形象模型
│   ├── schemas/
│   │   ├── voice.py                 # 语音数据模式
│   │   ├── dialogue.py              # 对话服务
│   │   ├── digital_human.py         # 数字人管理服务
│   │   └── avatar_builder.py        # 虚拟形象数据模式
│   └── services/
│       ├── voice.py                 # 语音服务
│       └── avatar_builder.py        # 虚拟形象构建服务
├── main.py                          # 应用入口
└── requirements.txt                 # 依赖管理
```

API将在 `http://localhost:8000` 上可用。
