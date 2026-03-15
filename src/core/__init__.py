"""
核心模块
Core Module

该模块提供核心功能，包括：
- 自定义异常
- 工具函数
- 日志配置

This module provides core functionality, including:
- Custom exceptions
- Utility functions
- Logging configuration
"""

from .exceptions import (
    StockAnalysisError,
    DataError,
    DataSourceError,
    DataNotFoundError,
    DataValidationError,
    DataCacheError,
    ModelError,
    ModelNotFoundError,
    ModelTrainingError,
    ModelPredictionError,
    AnalysisError,
    TechnicalAnalysisError,
    FactorAnalysisError,
    BacktestError,
    TradingError,
    InsufficientFundsError,
    InsufficientSharesError,
    OrderError,
    PositionError,
    ConfigurationError,
    ConfigNotFoundError,
    ConfigValidationError,
    handle_exception,
)

from .utils import (
    logger,
    setup_logger,
    timer,
    retry,
    log_execution,
    parse_date,
    get_trading_days,
    date_range_to_str,
    normalize_stock_code,
    safe_divide,
    calculate_returns,
    calculate_cumulative_returns,
    resample_data,
    format_number,
    format_percentage,
    format_money,
    format_volume,
    validate_stock_code,
    validate_date_range,
    ensure_dir,
    load_json,
    save_json,
)

__all__ = [
    # Exceptions
    "StockAnalysisError",
    "DataError",
    "DataSourceError",
    "DataNotFoundError",
    "DataValidationError",
    "DataCacheError",
    "ModelError",
    "ModelNotFoundError",
    "ModelTrainingError",
    "ModelPredictionError",
    "AnalysisError",
    "TechnicalAnalysisError",
    "FactorAnalysisError",
    "BacktestError",
    "TradingError",
    "InsufficientFundsError",
    "InsufficientSharesError",
    "OrderError",
    "PositionError",
    "ConfigurationError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "handle_exception",

    # Utilities
    "logger",
    "setup_logger",
    "timer",
    "retry",
    "log_execution",
    "parse_date",
    "get_trading_days",
    "date_range_to_str",
    "normalize_stock_code",
    "safe_divide",
    "calculate_returns",
    "calculate_cumulative_returns",
    "resample_data",
    "format_number",
    "format_percentage",
    "format_money",
    "format_volume",
    "validate_stock_code",
    "validate_date_range",
    "ensure_dir",
    "load_json",
    "save_json",
]