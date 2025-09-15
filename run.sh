#!/bin/bash

# Twitter 爬虫启动脚本
# 使用uv管理的Python环境运行Twitter爬虫

echo "🐦 Twitter爬虫工具"
echo "=================="

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: uv未安装。请先安装uv: https://github.com/astral-sh/uv"
    exit 1
fi

# 检查项目依赖是否已安装
if [ ! -d ".venv" ]; then
    echo "📦 首次运行，正在安装依赖..."
    uv sync
    echo "✅ 依赖安装完成"
fi

# 检查环境变量
if [ -z "$TWITTER_BEARER_TOKEN" ]; then
    echo "⚠️  警告: 未设置TWITTER_BEARER_TOKEN环境变量"
    echo "请设置Twitter API密钥:"
    echo "export TWITTER_BEARER_TOKEN='your_token_here'"
    echo ""
fi

# 显示配置信息
echo "📋 当前配置:"
echo "- Python版本: $(cat .python-version)"
echo "- 用户配置文件: users_config.txt"
echo ""

# 运行程序
echo "🚀 启动Twitter爬虫..."
uv run twitter-scraper