"""
配置模块
Configuration Module

该模块提供应用程序配置，包括：
- 数据源配置
- 模型配置
- 交易配置
- 缓存配置

This module provides application configuration, including:
- Data source configuration
- Model configuration
- Trading configuration
- Cache configuration
"""

from .settings import (
    # Paths
    PROJECT_ROOT,
    DATA_DIR,
    CACHE_DIR,
    QLIB_DATA_DIR,
    CONFIG_DIR,
    MODEL_DIR,
    SAVED_MODEL_DIR,
    LOG_DIR,

    # Configuration classes
    DataSourceConfig,
    ModelConfig,
    TradingConfig,
    CacheConfig,
    LogConfig,

    # Data source configuration
    DATA_SOURCES,
    get_data_source_config,
    get_enabled_data_sources,

    # Model configuration
    MODELS,
    DEFAULT_MODEL,
    get_model_config,
    get_enabled_models,

    # Trading configuration
    TRADING_CONFIG,

    # Cache configuration
    CACHE_CONFIG,

    # Logging configuration
    LOG_CONFIG,

    # Technical indicators
    TECHNICAL_INDICATORS,

    # Factors
    FACTORS,

    # Web configuration
    WEB_CONFIG,
)

__all__ = [
    # Paths
    "PROJECT_ROOT",
    "DATA_DIR",
    "CACHE_DIR",
    "QLIB_DATA_DIR",
    "CONFIG_DIR",
    "MODEL_DIR",
    "SAVED_MODEL_DIR",
    "LOG_DIR",

    # Configuration classes
    "DataSourceConfig",
    "ModelConfig",
    "TradingConfig",
    "CacheConfig",
    "LogConfig",

    # Data source configuration
    "DATA_SOURCES",
    "get_data_source_config",
    "get_enabled_data_sources",

    # Model configuration
    "MODELS",
    "DEFAULT_MODEL",
    "get_model_config",
    "get_enabled_models",

    # Trading configuration
    "TRADING_CONFIG",

    # Cache configuration
    "CACHE_CONFIG",

    # Logging configuration
    "LOG_CONFIG",

    # Technical indicators
    "TECHNICAL_INDICATORS",

    # Factors
    "FACTORS",

    # Web configuration
    "WEB_CONFIG",
]