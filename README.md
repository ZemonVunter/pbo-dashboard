# 中国人民银行 货币政策看板

![Vue 3](https://img.shields.io/badge/Vue-3-4.2.5-brightgreen)
![ECharts](https://img.shields.io/badge/ECharts-5.4.3-orange)
![Python](https://img.shields.io/badge/Python-3.11-blue)

实时跟踪中国央行公开市场操作，智能计算到期日，节假日自动顺延。

## ✨ 功能特性

- 📊 **实时看板**：今日到期、今日投放、净投放一目了然
- 🗓️ **智能日历**：未来30天到期压力可视化，周末/节假日标记
- 🔄 **自动顺延**：到期日遇周末/节假日自动推迟至下一工作日
- 📋 **操作记录**：完整历史数据表格，支持排序筛选
- 🎨 **美观界面**：Vue 3 + Element Plus + ECharts，响应式设计

## 🚀 快速开始

### 在线访问
直接访问 GitHub Pages（1-2分钟后生效）：
```
https://ZemonVunter.github.io/pbo-dashboard/
```

### 本地运行

#### 1. 克隆仓库
```bash
git clone https://github.com/ZemonVunter/pbo-dashboard.git
cd pbo-dashboard
```

#### 2. 安装依赖
```bash
pip install tushare chinese-calendar
```

#### 3. 配置 Tushare Token

编辑 `scripts/fetch_data.py`，修改 `TUSHARE_TOKEN`：
```python
TUSHARE_TOKEN = "你的_Tushare_Token"
```

#### 4. 运行数据抓取
```bash
python scripts/fetch_data.py
```

#### 5. 启动本地服务器
```bash
# 使用 Python
cd public
python -m http.server 8000

# 或使用 Node.js
npx serve public
```

访问：http://localhost:8000

## 📁 项目结构

```
pbo-dashboard/
├── public/
│   └── index.html           # Vue 3 前端（单文件）
├── scripts/
│   └── fetch_data.py        # Python 数据抓取脚本
├── data/
│   └── operations.json       # 生成的前端数据
└── README.md
```

## 🔧 技术栈

### 前端
- **Vue 3**：响应式框架（CDN 引入，无需构建）
- **Element Plus**：美观的 UI 组件库
- **ECharts**：专业的数据可视化图表

### 后端
- **Python 3**：数据处理与计算
- **Tushare**：专业财经数据接口
- **chinesecalendar**：中国法定节假日库

## 📊 数据说明

### 数据来源
- **Tushare API**：提供央行公开市场操作数据
- **更新延迟**：约 1-2 小时（官方公告延迟）

### 计算逻辑

1. **到期日计算**：$到期日期 = 公告日期 + 期限$
2. **节假日顺延**：
   - 如果到期日是周六/周日或法定假日
   - 自动推迟到下一个工作日
3. **净投放计算**：$净投放 = 今日投放 - 今日到期$

## 🎯 待优化项

明天购买 GLM Coding Plan 后，将完成以下优化：

- [ ] 真实对接 Tushare API（当前为示例数据）
- [ ] 添加自动刷新定时任务（每小时更新一次）
- [ ] 增加历史曲线图（90天趋势）
- [ ] 添加预警推送（到期金额 > 5000亿）
- [ ] 优化移动端显示

## 📄 许可证

MIT License

## 👨‍💻 作者

由 [OpenClaw](https://openclaw.ai) 自动化构建

---

**⚠️ 注意**：
- 如遇周末或节假日，到期日已自动顺延至下一工作日
- 数据可能存在 1-2 小时延迟
- 请勿用于实际投资决策，仅供参考
