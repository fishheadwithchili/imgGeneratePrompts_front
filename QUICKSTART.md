# 快速使用指南

## 🚀 快速开始

### 1. 启动后端API
确保你的Go后端API已经在运行：
```bash
cd D:\projects\GolandProjects\imgGeneratePrompts
go run main.go
```
后端应该在 `http://localhost:8080` 运行。

### 2. 启动前端

#### 方法一：使用启动脚本 (推荐)
```bash
cd D:\projects\pythonProject\imgGeneratePrompts_front

# 首次运行，配置环境变量
cp .env.example .env

# 启动应用
bash start.sh
# 或者
chmod +x start.sh && ./start.sh
```

#### 方法二：手动启动
```bash
cd D:\projects\pythonProject\imgGeneratePrompts_front

# 创建虚拟环境 (推荐)
python -m venv .venv
source .venv/Scripts/activate  # Git Bash

# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

### 3. 访问应用
打开浏览器访问: `http://localhost:7860`

## 📋 主要功能

### 仪表板
- 查看系统统计信息
- 监控API连接状态
- 查看最近的提示词

### 提示词管理
- **创建提示词**: 支持上传图片，填写详细信息
- **查看提示词**: 浏览所有提示词，支持筛选和分页
- **编辑提示词**: 修改提示词内容和属性
- **重复检查**: 检查提示词是否重复

### 标签管理
- **查看标签**: 浏览所有标签
- **创建标签**: 添加新标签
- **搜索标签**: 快速查找标签
- **删除标签**: 移除不需要的标签

### 高级搜索
- **标签搜索**: 根据一个或多个标签搜索提示词
- **组合搜索**: 支持多种筛选条件

## 🔧 配置说明

### 环境变量配置
复制并编辑 `.env` 文件：
```bash
cp .env.example .env
```

主要配置项：
- `API_BASE_URL`: 后端API地址（默认: http://localhost:8080）
- `GRADIO_SERVER_PORT`: 前端端口（默认: 7860）
- `GRADIO_SERVER_NAME`: 服务器主机名（默认: 0.0.0.0）
- `GRADIO_SHARE`: 是否启用公网分享（默认: False）

### 注意事项
- `.env` 文件包含敏感配置，不会被提交到Git
- 使用 Git Bash 获得最佳体验
- 建议使用虚拟环境

## ❓ 常见问题

**Q: 界面显示"API连接失败"**
A: 检查后端Go服务是否正在运行，确认端口8080没有被占用。

**Q: 图片上传失败**
A: 确认图片格式正确（jpg, png, gif等），文件大小不超过10MB。

**Q: 数据不显示**
A: 点击"刷新"按钮，或者检查后端数据库连接。

**Q: start.sh 脚本权限拒绝**
A: 运行 `chmod +x start.sh` 给脚本添加执行权限。

**Q: 找不到 .env 文件**
A: 运行 `cp .env.example .env` 创建环境配置文件。

## 📞 技术支持

如有问题，请检查：
1. 后端API服务状态
2. 数据库连接状态
3. 网络连接
4. 浏览器控制台错误信息
5. `.env` 文件配置正确性

## 🛠️ 开发环境建议

- 使用 Git Bash 作为主要终端
- 启用虚拟环境进行Python包管理
- 定期更新 `.gitignore` 以保护敏感文件
- 使用 `start.sh` 脚本保持环境一致性
