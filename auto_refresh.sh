#!/bin/bash
# 央行货币政策看板 - 自动刷新脚本
# 用法: ./auto_refresh.sh [间隔分钟数]

# 默认间隔：60分钟
INTERVAL=${1:-60}

echo "🔄 开始自动刷新央行货币政策数据..."
echo "⏱️  刷新间隔: ${INTERVAL} 分钟"
echo "📁 工作目录: $(pwd)"

while true; do
    echo ""
    echo "🕒 $(date '+%Y-%m-%d %H:%M:%S') - 开始刷新数据..."
    
    # 检查依赖是否安装
    if command -v python3 &> /dev/null; then
        # 运行数据抓取脚本
        if python3 scripts/fetch_data.py; then
            echo "✅ 数据刷新成功"
            
            # 如果是 GitHub Pages 环境，可以尝试提交更新
            if [ -d ".git" ]; then
                echo "📤 正在提交更新到 GitHub..."
                git add data/operations.json
                git commit -m "🔄 自动更新央行数据: $(date '+%Y-%m-%d %H:%M:%S')" || true
                git push origin gh-pages --force || true
                echo "✅ GitHub Pages 更新完成"
            fi
        else
            echo "❌ 数据刷新失败"
        fi
    else
        echo "❌ Python3 未安装，跳过刷新"
    fi
    
    echo "⏳ 等待 ${INTERVAL} 分钟后再次刷新..."
    sleep $((INTERVAL * 60))
done