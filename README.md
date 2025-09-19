# 图像生成提示词管理系统 - 前端

这是一个基于 Gradio 的前端应用，用于管理图像生成AI的提示词。该应用提供了一个用户友好的Web界面，可以与后端Go API进行交互。

## 功能特性

### 🎨 核心功能
- **提示词管理**: 创建、查看、编辑、删除提示词
- **图片上传**: 支持上传图片并与提示词关联
- **标签系统**: 创建和管理标签，支持标签搜索
- **高级搜索**: 根据关键词、标签、模型等多维度搜索
- **统计信息**: 实时显示系统统计数据和最近活动

### 📊 界面功能
1. **仪表板**: 系统概览和统计信息
2. **提示词管理**: 
   - 创建新提示词（支持图片上传）
   - 查看提示词列表（支持筛选）
   - 编辑和删除提示词
   - 重复检查功能
3. **标签管理**: 
   - 查看所有标签
   - 创建新标签
   - 删除标签
   - 搜索标签
4. **高级搜索**: 根据标签组合搜索提示词

## 安装和运行

### 环境要求
- Python 3.8+
- 后端API服务运行在 `http://localhost:8080`
- Git Bash (Windows) 或其他 Unix shell

### 快速开始

#### 方法一：使用启动脚本 (推荐)
1. **进入项目目录**
   ```bash
   cd D:\projects\pythonProject\imgGeneratePrompts_front
   ```

2. **配置环境变量 (首次运行)**
   ```bash
   # 复制环境变量模板文件
   cp .env.example .env
   
   # 根据需要编辑 .env 文件
   # 大多数情况下默认配置即可使用
   ```

3. **运行启动脚本**
   ```bash
   # 使用 Git Bash 或其他 Unix shell
   bash start.sh
   
   # 或者给脚本添加执行权限后直接运行
   chmod +x start.sh
   ./start.sh
   ```

#### 方法二：手动启动
1. **进入项目目录**
   ```bash
   cd D:\projects\pythonProject\imgGeneratePrompts_front
   ```

2. **创建虚拟环境 (推荐)**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Git Bash
   # 或者在 Windows CMD: .venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件根据需要修改配置
   ```

5. **启动应用**
   ```bash
   python app.py
   ```

6. **访问应用**
   打开浏览器访问: `http://localhost:7860`

## 项目结构

```
imgGeneratePrompts_front/
├── app.py              # 主应用文件
├── api_client.py       # API客户端
├── config.py           # 配置文件
├── requirements.txt    # 依赖包列表
├── .env.example        # 环境变量模板
├── .gitignore          # Git忽略文件
├── start.sh            # Git Bash 启动脚本
├── start.bat           # Windows 启动脚本（废弃）
└── README.md          # 项目说明
```

## 配置说明

### 环境变量配置

项目使用 `.env` 文件进行环境配置。**请注意：`.env` 文件包含敏感信息，已被添加到 `.gitignore` 中，不会被提交到版本控制。**

#### 配置步骤：
1. 复制环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 根据需要编辑 `.env` 文件中的配置项。

#### 主要配置项：
- `API_BASE_URL`: 后端API地址（默认: http://localhost:8080）
- `GRADIO_SERVER_NAME`: Gradio服务器主机名（默认: 0.0.0.0）
- `GRADIO_SERVER_PORT`: Gradio服务器端口（默认: 7860）
- `GRADIO_SHARE`: 是否启用Gradio分享链接（默认: False）

#### 常用配置场景：
```env
# 开发环境（默认）
API_BASE_URL=http://localhost:8080
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=False

# 生产环境示例
API_BASE_URL=http://your-backend-server:8080
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=False

# 测试环境（启用公网分享）
GRADIO_SHARE=True
```

## API接口对接

本前端应用完整对接了以下后端API接口：

### 提示词相关接口
- `POST /api/v1/prompts/` - 创建提示词
- `POST /api/v1/prompts/upload` - 上传图片并创建提示词
- `GET /api/v1/prompts/` - 获取提示词列表
- `GET /api/v1/prompts/public` - 获取公开提示词
- `GET /api/v1/prompts/recent` - 获取最近提示词
- `GET /api/v1/prompts/stats` - 获取统计信息
- `GET /api/v1/prompts/search/tags` - 根据标签搜索
- `GET /api/v1/prompts/check-duplicate` - 检查重复
- `GET /api/v1/prompts/:id` - 获取单个提示词
- `PUT /api/v1/prompts/:id` - 更新提示词
- `DELETE /api/v1/prompts/:id` - 删除提示词

### 标签相关接口
- `POST /api/v1/tags/` - 创建标签
- `GET /api/v1/tags/` - 获取所有标签
- `GET /api/v1/tags/search` - 搜索标签
- `GET /api/v1/tags/stats` - 获取标签统计
- `GET /api/v1/tags/:id` - 获取单个标签
- `DELETE /api/v1/tags/:id` - 删除标签

### 系统接口
- `GET /health` - 健康检查
- `GET /db-status` - 数据库状态检查

## 使用指南

### 1. 创建提示词
1. 进入"提示词管理" → "创建提示词"标签页
2. 填写必要信息（提示词文本为必填项）
3. 可选择上传相关图片
4. 添加标签（用逗号分隔）
5. 点击"创建提示词"按钮

### 2. 管理提示词
1. 在"查看提示词"标签页中浏览所有提示词
2. 使用筛选器进行搜索
3. 在"编辑提示词"标签页中修改或删除提示词

### 3. 标签管理
1. 在"标签管理"模块中查看所有标签
2. 创建新标签或删除不需要的标签
3. 使用搜索功能快速找到特定标签

### 4. 高级搜索
1. 使用"高级搜索"功能根据标签组合查找提示词
2. 支持多标签搜索（用逗号分隔）

## 重要文件说明

### 环境配置文件
- **`.env.example`**: 环境变量模板文件，包含所有可配置项的说明
- **`.env`**: 实际的环境配置文件（由用户创建，不提交到Git）
- **`.gitignore`**: Git忽略文件，防止敏感文件被提交

### 启动脚本
- **`start.sh`**: Git Bash/Unix Shell 启动脚本（推荐使用）
- **`start.bat`**: Windows 批处理文件（已废弃，建议删除）

### 为什么使用 Git Bash？
1. **跨平台兼容性**: Shell 脚本可以在 Linux/macOS/Windows 上运行
2. **更好的环境管理**: 支持虚拟环境和环境变量
3. **现代开发流程**: 与现代Python开发流程一致

## 故障排除

### 连接问题
1. 确认后端API服务正在运行
2. 检查API地址配置是否正确
3. 查看浏览器控制台是否有错误信息

### 图片上传问题
1. 确认图片格式支持（jpg, jpeg, png, gif, bmp）
2. 检查图片大小是否超过限制（默认10MB）
3. 确认后端uploads目录权限正确

### 界面问题
1. 刷新浏览器页面
2. 清除浏览器缓存
3. 检查网络连接

### Git Bash 相关问题
1. **权限问题**: 如果遇到权限拒绝，运行 `chmod +x start.sh`
2. **脚本不运行**: 确保使用 `bash start.sh` 命令
3. **路径问题**: 确保在项目根目录下运行命令
4. **环境变量问题**: 检查 `.env` 文件是否存在和配置正确

## 开发说明

### 添加新功能
1. 在 `api_client.py` 中添加新的API调用方法
2. 在 `app.py` 中添加对应的界面组件和事件处理
3. 更新配置文件（如需要）

### 自定义样式
可以在 `app.py` 中的 `custom_css` 变量中添加自定义CSS样式。

## 许可证

本项目遵循 MIT 许可证。

## 支持

如有问题或建议，请联系开发团队。
