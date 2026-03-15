"""
全局配置模块
Global Configuration Module

该模块定义了整个应用程序的配置项，包括：
- 数据源配置
- 模型配置
- 交易配置
- 缓存配置

This module defines all configuration items for the application, including:
- Data source configuration
- Model configuration
- Trading configuration
- Cache configuration
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv

# 加载环境变量 / Load environment variables
load_dotenv()


# ==================== 路径配置 / Path Configuration ====================

# 项目根目录 / Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 数据目录 / Data directory
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = Path(os.getenv("CACHE_DIR", DATA_DIR / "cache"))
QLIB_DATA_DIR = Path(os.getenv("QLIB_DATA_PATH", DATA_DIR / "qlib_data"))

# 配置目录 / Config directory
CONFIG_DIR = PROJECT_ROOT / "config"

# 模型目录 / Models directory
MODEL_DIR = PROJECT_ROOT / "models"
SAVED_MODEL_DIR = Path(os.getenv("MODEL_DIR", MODEL_DIR / "saved"))

# 日志目录 / Logs directory
LOG_DIR = PROJECT_ROOT / "logs"

# 确保目录存在 / Ensure directories exist
for directory in [DATA_DIR, CACHE_DIR, QLIB_DATA_DIR, MODEL_DIR, SAVED_MODEL_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ==================== 数据库配置 / Database Configuration ====================

@dataclass
class DatabaseConfig:
    """
    MySQL 数据库配置类
    MySQL Database Configuration Class

    Attributes:
        host: MySQL 服务器地址 / MySQL server host
        port: MySQL 端口 / MySQL port
        user: 用户名 / Username
        password: 密码 / Password
        database: 数据库名 / Database name
    """
    host: str = os.getenv("MYSQL_HOST", "localhost")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    user: str = os.getenv("MYSQL_USER", "root")
    password: str = os.getenv("MYSQL_PASSWORD", "")
    database: str = os.getenv("MYSQL_DATABASE", "stock_analysis")

    @property
    def connection_url(self) -> str:
        """获取 MySQL 连接 URL / Get MySQL connection URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"


# 数据库配置实例 / Database configuration instance
DATABASE_CONFIG = DatabaseConfig()


# ==================== 数据源配置 / Data Source Configuration ====================

@dataclass
class DataSourceConfig:
    """
    数据源配置类
    Data Source Configuration Class

    Attributes:
        name: 数据源名称 / Data source name
        enabled: 是否启用 / Whether enabled
        priority: 优先级（数值越小优先级越高） / Priority (lower value means higher priority)
        api_key: API密钥 / API key
        rate_limit: 请求频率限制 / Rate limit (requests per minute)
    """
    name: str
    enabled: bool = True
    priority: int = 1
    api_key: Optional[str] = None
    rate_limit: int = 100
    extra_params: Dict[str, Any] = field(default_factory=dict)


# 数据源配置字典 / Data source configuration dictionary
DATA_SOURCES: Dict[str, DataSourceConfig] = {
    "qlib": DataSourceConfig(
        name="qlib",
        enabled=True,
        priority=1,
        extra_params={"region": "cn"}
    ),
    "tushare": DataSourceConfig(
        name="tushare",
        enabled=bool(os.getenv("TUSHARE_TOKEN")),
        priority=2,  # Tushare 作为主要数据源 / Tushare as primary data source
        api_key=os.getenv("TUSHARE_TOKEN"),
        rate_limit=200
    ),
    "akshare": DataSourceConfig(
        name="akshare",
        enabled=True,
        priority=3,  # AkShare 作为备用数据源 / AkShare as backup data source
        rate_limit=100
    )
}


# ==================== 模型配置 / Model Configuration ====================

@dataclass
class ModelConfig:
    """
    模型配置类
    Model Configuration Class

    Attributes:
        name: 模型名称 / Model name
        model_type: 模型类型 / Model type
        enabled: 是否启用 / Whether enabled
        params: 模型参数 / Model parameters
    """
    name: str
    model_type: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


# 模型配置字典 / Model configuration dictionary
MODELS: Dict[str, ModelConfig] = {
    "lightgbm": ModelConfig(
        name="LightGBM",
        model_type="gradient_boosting",
        enabled=True,
        params={
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "n_estimators": 1000,
            "early_stopping_rounds": 50
        }
    ),
    "mlp": ModelConfig(
        name="MLP",
        model_type="neural_network",
        enabled=True,
        params={
            "hidden_sizes": [256, 128, 64],
            "dropout": 0.2,
            "learning_rate": 0.001,
            "batch_size": 256,
            "epochs": 100
        }
    ),
    "transformer": ModelConfig(
        name="Transformer",
        model_type="transformer",
        enabled=True,
        params={
            "d_model": 64,
            "nhead": 4,
            "num_layers": 2,
            "dim_feedforward": 256,
            "dropout": 0.1,
            "learning_rate": 0.0001,
            "batch_size": 128,
            "epochs": 50
        }
    )
}

# 默认模型 / Default model
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "lightgbm")


# ==================== 交易配置 / Trading Configuration ====================

@dataclass
class TradingConfig:
    """
    交易配置类
    Trading Configuration Class

    Attributes:
        initial_capital: 初始资金 / Initial capital
        commission_rate: 佣金费率 / Commission rate
        stamp_duty_rate: 印花税率 / Stamp duty rate
        min_commission: 最低佣金 / Minimum commission
        slippage: 滑点 / Slippage
    """
    initial_capital: float = float(os.getenv("INITIAL_CAPITAL", 1000000))
    commission_rate: float = float(os.getenv("COMMISSION_RATE", 0.0003))
    stamp_duty_rate: float = float(os.getenv("STAMP_DUTY_RATE", 0.001))
    min_commission: float = 5.0  # 最低佣金5元 / Minimum commission 5 yuan
    slippage: float = 0.001  # 滑点0.1% / Slippage 0.1%


TRADING_CONFIG = TradingConfig()


# ==================== 缓存配置 / Cache Configuration ====================

@dataclass
class CacheConfig:
    """
    缓存配置类
    Cache Configuration Class

    Attributes:
        enabled: 是否启用缓存 / Whether cache is enabled
        ttl: 缓存有效期（秒） / Cache TTL in seconds
        max_size: 最大缓存大小（MB） / Maximum cache size in MB
    """
    enabled: bool = True
    ttl: int = int(os.getenv("CACHE_TTL", 86400))  # 默认1天 / Default 1 day
    max_size: int = 1000  # 最大缓存1000MB / Maximum 1000MB cache


CACHE_CONFIG = CacheConfig()


# ==================== 日志配置 / Logging Configuration ====================

@dataclass
class LogConfig:
    """
    日志配置类
    Log Configuration Class

    Attributes:
        level: 日志级别 / Log level
        format: 日志格式 / Log format
        file: 日志文件路径 / Log file path
        rotation: 日志轮转 / Log rotation
    """
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    file: Path = LOG_DIR / "stock_analysis.log"
    rotation: str = "10 MB"
    retention: str = "7 days"


LOG_CONFIG = LogConfig()


# ==================== 技术指标配置 / Technical Indicator Configuration ====================

# 常用技术指标参数 / Common technical indicator parameters
TECHNICAL_INDICATORS = {
    # 移动平均线 / Moving Averages
    "ma_periods": [5, 10, 20, 60, 120, 250],

    # 布林带 / Bollinger Bands
    "bollinger_period": 20,
    "bollinger_std": 2,

    # RSI / Relative Strength Index
    "rsi_period": 14,

    # MACD
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,

    # KDJ
    "kdj_n": 9,
    "kdj_m1": 3,
    "kdj_m2": 3,

    # ATR / Average True Range
    "atr_period": 14,

    # 成交量移动平均 / Volume Moving Average
    "volume_ma_periods": [5, 10, 20]
}


# ==================== 因子配置 / Factor Configuration ====================

# 常用因子列表 / Common factor list
FACTORS = {
    "value": ["pe_ratio", "pb_ratio", "ps_ratio", "pcf_ratio"],
    "growth": ["revenue_growth", "profit_growth", "roe", "roa"],
    "quality": ["gross_margin", "net_margin", "debt_ratio", "current_ratio"],
    "momentum": ["return_1m", "return_3m", "return_6m", "return_12m"],
    "volatility": ["volatility_20d", "volatility_60d", "beta"]
}


# ==================== Web界面配置 / Web Interface Configuration ====================

WEB_CONFIG = {
    "page_title": "中国股市AI分析系统",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "theme": {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#262730",
        "font": "sans serif"
    }
}


# ==================== 辅助函数 / Helper Functions ====================

def get_data_source_config(name: str) -> Optional[DataSourceConfig]:
    """
    获取数据源配置
    Get data source configuration

    Args:
        name: 数据源名称 / Data source name

    Returns:
        数据源配置，如果不存在返回None / Data source configuration, None if not exists
    """
    return DATA_SOURCES.get(name)


def get_model_config(name: str) -> Optional[ModelConfig]:
    """
    获取模型配置
    Get model configuration

    Args:
        name: 模型名称 / Model name

    Returns:
        模型配置，如果不存在返回None / Model configuration, None if not exists
    """
    return MODELS.get(name)


def get_enabled_data_sources() -> Dict[str, DataSourceConfig]:
    """
    获取所有启用的数据源
    Get all enabled data sources

    Returns:
        启用的数据源字典 / Dictionary of enabled data sources
    """
    return {k: v for k, v in DATA_SOURCES.items() if v.enabled}


def get_enabled_models() -> Dict[str, ModelConfig]:
    """
    获取所有启用的模型
    Get all enabled models

    Returns:
        启用的模型字典 / Dictionary of enabled models
    """
    return {k: v for k, v in MODELS.items() if v.enabled}