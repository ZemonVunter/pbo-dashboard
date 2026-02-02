#!/bin/bash
# 安装依赖包脚本

echo "🔧 开始安装依赖包..."

# 检查是否有 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3，尝试安装..."
    
    # 尝试不同的包管理器
    if command -v apt-get &> /dev/null; then
        echo "📦 使用 apt 安装 pip3..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        echo "📦 使用 yum 安装 pip3..."
        sudo yum install -y python3-pip
    else
        echo "❌ 无法找到合适的包管理器"
        echo "💡 请手动安装 python3-pip"
        exit 1
    fi
fi

# 安装 Python 依赖
echo "📦 安装 Python 包..."
pip3 install --user tushare chinese-calendar pandas requests

echo "✅ 依赖安装完成！"
echo ""
echo "🚀 现在可以运行数据抓取脚本："
echo "   python3 scripts/fetch_data.py"
echo ""
echo "📋 如果遇到权限问题，可以尝试："
echo "   pip3 install --user tushare"