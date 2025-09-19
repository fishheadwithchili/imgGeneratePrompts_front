#!/bin/bash

echo "========================================"
echo "    图像生成提示词管理系统 - 前端"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python &> /dev/null; then
    echo "错误: 未检测到Python环境"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

echo "Python版本: $(python --version)"
echo

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "⚠️  建议使用虚拟环境"
    echo "可以运行以下命令创建和激活虚拟环境:"
    echo "  python -m venv .venv"
    echo "  source .venv/Scripts/activate  # Git Bash"
    echo
fi

# 检查环境变量文件
if [[ ! -f ".env" ]]; then
    echo "⚠️  未找到 .env 文件"
    echo "建议复制 .env.example 为 .env 并根据需要修改配置"
    echo "  cp .env.example .env"
    echo
fi

echo "正在检查依赖包..."
# 安装依赖
pip install -r requirements.txt

echo
echo "正在启动前端应用..."
echo "请确保后端API服务已经在 http://localhost:8080 运行"
echo "前端将运行在: http://localhost:7860"
echo

# 启动应用
python app.py
