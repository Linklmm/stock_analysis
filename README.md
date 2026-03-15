# 中国股市 AI 分析系统

基于 Streamlit 和 qlib 构建的中国 A 股量化分析平台，提供实时行情、技术分析、财报分析、趋势预测、策略回测和模拟交易等功能。

## 功能特性

### 📊 市场概览
- 实时行情数据展示（上证指数、深证成指、创业板指）
- 涨跌停统计、市场情绪分析
- 自选股管理（添加、删除、分组）
- 市场资讯（财经新闻、涨停板、最新公告）

### 📈 技术分析
- K 线图可视化（支持 MA 均线、成交量）
- 多种技术指标：MACD、RSI、KDJ、布林带
- 自动生成交易信号（买入/卖出/持有）
- 综合信号评分系统

### 📑 财报分析
- 获取近 5 年财务数据
- 盈利能力分析（ROE、毛利率、净利率）
- 成长能力分析（营收/净利润增长率）
- 财务风险评估（资产负债率）
- 综合健康度评分

### 🔮 趋势预测
- 基于 LightGBM 的趋势预测模型
- 涨跌概率分析
- 多因子综合预测

### 🔬 因子分析
- 多因子暴露分析
- 因子相关性分析
- 因子收益预测

### ⏱️ 策略回测
- 自定义交易策略
- 回测绩效分析
- 收益曲线可视化

### 💼 组合管理
- 资产配置优化
- 风险收益分析
- 持仓管理

### 💰 模拟交易
- 模拟账户管理
- 实时委托下单
- 持仓盈亏计算
- 交易历史记录

## 项目结构

```
stock_analysis/
├── app.py                    # 应用入口
├── requirements.txt          # 依赖列表
├── .env.example              # 环境变量示例
│
├── config/
│   └── settings.py           # 配置管理
│
├── src/
│   ├── core/                 # 核心工具
│   │   ├── utils.py          # 通用工具函数
│   │   └── exceptions.py     # 自定义异常
│   │
│   ├── data/                 # 数据层
│   │   ├── database.py       # 数据库模型
│   │   ├── realtime.py       # 实时数据获取
│   │   ├── financial_report.py # 财报数据
│   │   ├── market_news.py    # 市场资讯
│   │   └── providers/        # 数据提供者
│   │
│   ├── analysis/             # 分析模块
│   │   ├── technical/        # 技术指标
│   │   ├── prediction/       # 预测模型
│   │   ├── factors/          # 因子分析
│   │   ├── backtest/         # 回测框架
│   │   └── risk/             # 风险分析
│   │
│   ├── models/               # 机器学习模型
│   │
│   ├── optimization/         # 组合优化
│   │
│   ├── trading/              # 模拟交易
│   │
│   └── web/                  # Web 界面
│       ├── 主页.py            # 主页面
│       ├── components/       # UI 组件
│       └── pages/            # 子页面
│
└── scripts/
    └── init_database.py      # 数据库初始化
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- TA-Lib（需要先安装系统依赖）

### 2. 安装依赖

```bash
# macOS 安装 TA-Lib
brew install ta-lib

# Ubuntu 安装 TA-Lib
sudo apt-get install ta-lib

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
vim .env
```

配置内容：

```ini
# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=stock_analysis

# Tushare Token（可选，用于增强数据源）
TUSHARE_TOKEN=your_token
```

### 4. 初始化数据库

```bash
python scripts/init_database.py
```

### 5. 启动应用

```bash
python app.py
```

或指定端口：

```bash
python app.py --port 8502
```

## 数据来源

| 数据类型 | 主要来源 | 备用来源 |
|---------|---------|---------|
| 实时行情 | AkShare | Tushare |
| 财务数据 | AkShare | Tushare |
| 股票信息 | AkShare | Tushare |
| 市场资讯 | AkShare | - |

AkShare 无需 Token 即可使用，Tushare 需要申请 Token。

## 技术栈

- **前端框架**: Streamlit
- **数据可视化**: Plotly
- **量化框架**: qlib
- **技术分析**: TA-Lib
- **机器学习**: LightGBm, PyTorch, scikit-learn
- **数据存储**: MySQL, SQLAlchemy
- **数据源**: AkShare, Tushare

## 开发说明

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_module.py

# 带覆盖率报告
pytest --cov=src tests/
```

### 代码规范

- 使用 `black` 格式化代码
- 使用 `isort` 整理导入
- 使用 `flake8` 检查代码风格

```bash
black src/
isort src/
flake8 src/
```

## 许可证

MIT License

## 致谢

- [AkShare](https://github.com/akfamily/akshare) - 开源金融数据接口
- [Tushare](https://tushare.pro/) - 金融数据接口
- [qlib](https://github.com/microsoft/qlib) - 微软量化投资平台
- [Streamlit](https://streamlit.io/) - 数据应用框架