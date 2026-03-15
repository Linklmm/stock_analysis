"""
中国股市 AI 分析系统
Chinese Stock Market AI Analysis System

基于 qlib 的量化分析平台，提供：
- 趋势预测
- 技术分析
- 因子分析
- 策略回测
- 组合优化
- 模拟交易

A quantitative analysis platform based on qlib, providing:
- Trend prediction
- Technical analysis
- Factor analysis
- Strategy backtesting
- Portfolio optimization
- Paper trading
"""

__version__ = "1.0.0"
__author__ = "Stock Analysis Team"

# 导入主要模块
from src.core import (
    # Exceptions
    StockAnalysisError,
    DataError,
    ModelError,
    AnalysisError,
    TradingError,

    # Utilities
    logger,
    normalize_stock_code,
    parse_date,
)

from src.data import (
    # Base
    DataProvider,
    DataFrequency,
    StockInfo,

    # Cache
    cache,
    cached,

    # Processor
    DataProcessor,
    process_data,
)

from src.analysis import (
    AnalysisEngine,
    AnalysisResult,
    create_engine,
)

from src.models import (
    ModelManager,
    get_model_manager,
    train_model,
    predict,
)

from src.trading import (
    PaperAccount,
    PaperBroker,
    Order,
    Position,
)

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Exceptions
    "StockAnalysisError",
    "DataError",
    "ModelError",
    "AnalysisError",
    "TradingError",

    # Utilities
    "logger",
    "normalize_stock_code",
    "parse_date",

    # Data
    "DataProvider",
    "DataFrequency",
    "StockInfo",
    "cache",
    "cached",
    "DataProcessor",
    "process_data",

    # Analysis
    "AnalysisEngine",
    "AnalysisResult",
    "create_engine",

    # Models
    "ModelManager",
    "get_model_manager",
    "train_model",
    "predict",

    # Trading
    "PaperAccount",
    "PaperBroker",
    "Order",
    "Position",
]