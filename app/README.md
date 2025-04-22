# AD Caregiver 数字人应用

## 项目概述

AD Caregiver 是一个基于人工智能的数字人应用，专为阿尔茨海默病患者及其照护者设计。该应用通过语音交互、情感支持和认知训练等功能，为患者提供全天候的陪伴和支持，同时减轻照护者的负担。

## 功能特点

- **语音交互**：支持自然语言对话，患者可以通过语音与数字人进行交流
- **情感支持**：数字人能够识别患者情绪，提供适当的安慰和支持
- **认知训练**：提供记忆游戏、简单问答等认知训练活动
- **照护者支持**：为照护者提供患者状态监测、照护建议和资源
- **个性化体验**：根据患者需求和偏好定制交互内容和方式
- **多语言支持**：支持中文和英文等多种语言

## 技术架构

### 后端技术栈

- **FastAPI**：高性能的Python Web框架，用于构建API
- **SQLAlchemy**：ORM框架，用于数据库操作
- **Pydantic**：数据验证和设置管理
- **Vosk**：语音识别引擎，支持中文语音转文本
- **OpenAI API**：用于生成自然语言回复
- **SiliconFlow API**：用于文本转语音合成
- **异步编程**：使用Python的asyncio和aiofiles实现异步操作

### 前端技术栈

- **React**：用于构建用户界面
- **TypeScript**：提供类型安全
- **Tailwind CSS**：用于样式设计
- **Web Audio API**：处理音频播放和录制

### 数据存储

- **SQLite**：本地数据库，存储用户信息和交互历史
- **文件系统**：存储音频文件和模型数据

## 系统要求

- Python 3.8+
- Node.js 14+
- 足够的磁盘空间用于存储音频文件和模型（约2GB）
- 麦克风和扬声器（用于语音交互）

## 安装指南

### 后端设置

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/ad-caregiver.git
   cd ad-caregiver
   ```

2. 创建并激活虚拟环境：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   创建`.env`文件并设置以下变量：
   ```
   TTS_BASE_URL=https://api.siliconflow.cn/v1
   TTS_API_KEY=your_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. 初始化数据库：
   ```bash
   python scripts/init_db.py
   ```

### 前端设置

1. 进入前端目录：
   ```bash
   cd frontend
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 构建前端：
   ```bash
   npm run build
   ```

## 启动应用

### 开发模式

1. 启动后端服务：
   ```bash
   uvicorn main:app --reload
   ```

2. 启动前端开发服务器：
   ```bash
   cd frontend
   npm run dev
   ```

### 生产模式

1. 构建前端：
   ```bash
   cd frontend
   npm run build
   ```

2. 启动生产服务器：
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 项目结构

```
ad-caregiver/
├── app/                    # 应用主目录
│   ├── api/                # API路由
│   │   ├── endpoints/      # API端点
│   │   └── deps.py         # 依赖注入
│   ├── core/               # 核心配置
│   │   ├── config.py       # 配置管理
│   │   └── security.py     # 安全相关
│   ├── db/                 # 数据库
│   │   ├── app_db.py       # 数据库管理
│   │   └── models.py       # 数据模型
│   ├── services/           # 服务层
│   │   ├── voice.py        # 语音服务
│   │   ├── deepseek.py     # AI对话服务
│   │   └── digital_human.py # 数字人服务
│   ├── static/             # 静态文件
│   │   ├── audio/          # 音频文件
│   │   └── models/         # 模型文件
│   ├── utils/              # 工具函数
│   ├── main.py             # 应用入口
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端代码
│   ├── public/             # 公共资源
│   ├── src/                # 源代码
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面
│   │   ├── services/       # 前端服务
│   │   └── App.tsx         # 主应用
│   ├── package.json        # 前端依赖
│   └── tsconfig.json       # TypeScript配置
├── scripts/                # 脚本文件
├── tests/                  # 测试代码
├── .env                    # 环境变量
├── .gitignore              # Git忽略文件
└── README.md               # 项目文档
```

## API文档

### 数字人API

- `GET /api/digital-humans`：获取所有数字人列表
- `GET /api/digital-humans/{id}`：获取特定数字人详情
- `POST /api/digital-humans`：创建新数字人
- `PUT /api/digital-humans/{id}`：更新数字人信息
- `DELETE /api/digital-humans/{id}`：删除数字人

### 语音交互API

- `POST /api/voice/transcribe`：将音频转换为文本
- `POST /api/voice/generate`：生成语音回复
- `POST /api/voice/upload`：上传训练音频
- `POST /api/voice/train`：训练数字人音色

### 对话API

- `POST /api/chat`：发送消息并获取回复
- `GET /api/chat/history`：获取对话历史

## 使用指南

### 数字人创建

1. 登录系统后，点击"创建数字人"按钮
2. 填写数字人基本信息（名称、性别、年龄等）
3. 上传数字人头像
4. 上传训练音频（用于训练数字人音色）
5. 选择数字人性格特征和交互风格
6. 点击"创建"完成数字人创建

### 语音交互

1. 在数字人界面点击"开始对话"按钮
2. 允许麦克风访问权限
3. 开始与数字人对话
4. 数字人会通过语音回复您的问题
5. 对话结束后点击"结束对话"按钮

### 认知训练

1. 在数字人界面选择"认知训练"功能
2. 选择训练类型（记忆游戏、简单问答等）
3. 按照提示完成训练
4. 查看训练结果和进度

## 开发指南

### 添加新功能

1. 在`services`目录下创建新的服务文件
2. 在`api/endpoints`目录下创建新的API端点
3. 在`db/models.py`中添加新的数据模型（如需要）
4. 在前端添加相应的组件和页面
5. 更新API文档

### 代码风格

- 后端遵循PEP 8规范
- 前端使用ESLint和Prettier进行代码格式化
- 所有函数和类都应该有文档字符串
- 使用类型注解提高代码可读性

## 测试

### 后端测试

```bash
pytest
```

### 前端测试

```bash
cd frontend
npm test
```

## 部署

### Docker部署

1. 构建Docker镜像：
   ```bash
   docker build -t ad-caregiver .
   ```

2. 运行容器：
   ```bash
   docker run -p 8000:8000 ad-caregiver
   ```

### 云服务器部署

1. 在云服务器上安装所需依赖
2. 克隆代码仓库
3. 配置环境变量
4. 使用Nginx作为反向代理
5. 使用Gunicorn或Uvicorn作为WSGI服务器

## 常见问题

### 音频问题

**Q: 为什么我的麦克风无法工作？**
A: 请确保您的浏览器已获得麦克风访问权限，并且您的设备麦克风正常工作。

**Q: 为什么生成的语音质量不佳？**
A: 请确保您的网络连接稳定，并且上传的训练音频质量良好（16kHz采样率，16位深度，单声道）。

### 性能问题

**Q: 应用运行缓慢怎么办？**
A: 请确保您的设备满足最低系统要求，并关闭不必要的后台应用程序。

**Q: 语音识别不准确怎么办？**
A: 请确保您的环境噪音较低，并尽量使用清晰的语音进行交互。

## 贡献指南

1. Fork项目仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅LICENSE文件

## 联系方式

- 项目负责人：[姓名]
- 电子邮件：[邮箱地址]
- 项目链接：[GitHub仓库链接]

## 致谢

感谢所有为本项目做出贡献的开发者、测试者和用户。特别感谢以下开源项目：

- FastAPI
- React
- Vosk
- OpenAI
- SiliconFlow 