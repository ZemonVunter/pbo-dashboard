# 🎯 获取真实央行数据指南

## 📋 当前状态
- ✅ **网站已部署**：https://ZemonVunter.github.io/pbo-dashboard/
- ✅ **模拟数据**：当前使用模拟数据，界面完整可用
- ⏳ **真实数据**：需要安装 Tushare 依赖

## 🚀 获取真实数据步骤

### 方法一：自动安装（推荐）
```bash
# 进入项目目录
cd projects/pbo-dashboard

# 运行自动安装脚本
bash install_deps.sh

# 运行数据抓取
python3 scripts/fetch_data.py
```

### 方法二：手动安装
```bash
# 1. 安装 Python 依赖
pip3 install tushare chinese-calendar pandas requests

# 2. 运行数据抓取
python3 scripts/fetch_data.py
```

### 方法三：Docker 环境（如果有）
```bash
# 如果您有 Docker 环境，可以这样运行
docker run -v $(pwd):/app python:3.9 bash -c "
cd /app && pip install tushare && python scripts/fetch_data.py
"
```

## 📊 数据说明

### Tushare API 支持
脚本会尝试以下接口：
1. `central_bank_daily` - 央行每日操作
2. `money_flow` - 资金流动数据

### 数据源标识
- **真实数据**：显示 `数据源: tushare`
- **模拟数据**：显示 `数据源: mock`

## 🔧 故障排除

### 问题1：权限错误
```bash
# 尝试用户级安装
pip3 install --user tushare
```

### 问题2：网络连接问题
```bash
# 检查网络连接
curl -I https://api.tushare.com

# 如果无法访问，可能需要配置代理
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```

### 问题3：Token 无效
- 检查您的 Tushare Token 是否正确
- 确认 Token 是否在有效期内
- 访问 https://tushare.pro 查看账户状态

## 🎉 完成后的效果

安装成功后，您将看到：
- ✅ 真实的央行操作数据
- ✅ 准确的到期日计算
- ✅ 实时的净投放统计
- ✅ 历史操作记录

## 📞 支持

如果遇到问题，请检查：
1. 网络连接是否正常
2. Python 版本是否 >= 3.7
3. Tushare Token 是否有效
4. 是否有足够的 API 调用次数

---

**🎊 项目已准备就绪，只需安装依赖即可获取真实数据！**