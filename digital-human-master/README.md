# 数字人聊天前端项目

## 项目概述
这是一个基于 Vue 3 + uni-app 开发的数字人聊天应用前端项目。该应用允许用户与数字人进行语音交互，支持数字人的训练、管理和切换等功能。

## 功能特性

### 1. 数字人管理
- 添加新的数字人
- 编辑数字人信息
- 删除数字人
- 查看数字人列表
- 切换当前对话的数字人

### 2. 语音交互
- 实时语音录制
- 语音波形动画显示
- 上滑取消录音
- 自动播放数字人回复
- 录音时长显示

### 3. 训练功能
- 上传训练音频
- 训练状态实时显示
- 训练进度追踪
- 训练完成通知

### 4. 界面定制
- 多种背景颜色切换
- 响应式布局设计
- 流畅的动画效果
- 直观的状态提示

### 5. 用户管理
- 用户登录/注册
- 个人信息管理
- 退出登录功能

## 技术栈

### 前端框架
- Vue 3
- uni-app
- Vite
- Vue Router
- Pinia (状态管理)

### UI 组件
- uni-ui
- 自定义组件

### 工具库
- Axios (HTTP 请求)
- dayjs (日期处理)

### 开发工具
- VS Code
- HBuilderX
- Chrome DevTools

## 项目结构
```
src/
├── api/                # API 接口定义
├── components/         # 公共组件
├── pages/             # 页面文件
│   ├── index/         # 首页
│   ├── login/         # 登录页
│   ├── manage/        # 管理页
│   └── profile/       # 个人中心
├── static/            # 静态资源
├── store/             # 状态管理
├── utils/             # 工具函数
└── App.vue            # 应用入口
```

## 安装说明

### 环境要求
- Node.js >= 14.0.0
- npm >= 6.0.0
- HBuilderX (推荐)

### 安装步骤
1. 克隆项目
```bash
git clone [项目地址]
```

2. 安装依赖
```bash
npm install
```

3. 运行开发服务器
```bash
npm run dev
```

4. 打包发布
```bash
npm run build
```

## 使用说明

### 开发模式
1. 启动开发服务器
```bash
npm run dev
```

2. 在浏览器中访问
```
http://localhost:5173
```

### 生产部署
1. 构建生产版本
```bash
npm run build
```

2. 部署 dist 目录到服务器

## API 接口说明

### 数字人相关接口
- `GET /api/v1/digital/list` - 获取数字人列表
- `POST /api/v1/digital/create` - 创建数字人
- `PUT /api/v1/digital/{id}` - 更新数字人信息
- `DELETE /api/v1/digital/{id}` - 删除数字人

### 训练相关接口
- `POST /api/v1/digital/train/{id}` - 提交训练任务
- `GET /api/v1/digital/train/status/{id}` - 获取训练状态
- `POST /api/v1/digital/generate/{id}` - 生成语音

### 文件上传接口
- `POST /api/v1/files/upload/training-audio` - 上传训练音频
- `POST /api/v1/files/upload/recorded-audio` - 上传录音文件

## 开发指南

### 代码规范
- 使用 ESLint 进行代码检查
- 遵循 Vue 3 组合式 API 风格
- 使用 TypeScript 类型注解（可选）

### 组件开发
- 组件命名采用 PascalCase
- 使用组合式 API 编写组件
- 保持组件的单一职责

### 状态管理
- 使用 Pinia 进行状态管理
- 按功能模块划分 store
- 保持状态的可预测性

## 常见问题

### 1. 音频播放问题
- 确保浏览器支持 Web Audio API
- 检查音频文件格式是否支持
- 验证音频 URL 是否可访问

### 2. 录音功能问题
- 确保已授予麦克风权限
- 检查浏览器兼容性
- 验证录音设备是否正常

### 3. 跨域问题
- 配置正确的 CORS 策略
- 使用代理服务器
- 检查 API 域名配置

## 更新日志

### v1.0.0 (2024-03-xx)
- 初始版本发布
- 实现基本的数字人管理功能
- 支持语音交互功能
- 添加训练功能
- 实现界面定制功能

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
MIT License

## 联系方式
- 项目负责人：[姓名]
- 邮箱：[邮箱地址]
- 项目地址：[项目 URL] 