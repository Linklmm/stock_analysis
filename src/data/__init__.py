"""
数据层模块
Data Layer Module

该模块提供数据访问和处理功能，包括：
- 数据提供者抽象基类
- 多种数据源支持（qlib、Tushare、AkShare）
- 数据缓存
- 数据预处理

This module provides data access and processing functionality, including:
- Abstract base class for data providers
- Multiple data source support (qlib, Tushare, AkShare)
- Data caching
- Data preprocessing
"""

from .base import (
    DataProvider,
    DataProviderManager,
    DataFrequency,
    DataType,
    StockInfo,
    MarketData,
    standardize_columns,
    ensure_datetime_index
)

from .cache import (
    DataCache,
    DataFrameCache,
    CacheKey,
    cache,
    df_cache,
    cached,
    clear_all_cache,
    get_cache_stats
)

from .processor import (
    DataProcessor,
    process_data
)

# 数据提供者延迟导入 / Lazy import for data providers
def get_qlib_provider():
    """获取 qlib 数据提供者"""
    from .providers.qlib_provider import QlibDataProvider, create_qlib_provider
    return QlibDataProvider, create_qlib_provider


def get_tushare_provider():
    """获取 Tushare 数据提供者"""
    from .providers.tushare_provider import TushareDataProvider
    return TushareDataProvider


def get_akshare_provider():
    """获取 AkShare 数据提供者"""
    from .providers.akshare_provider import AkShareDataProvider
    return AkShareDataProvider


__all__ = [
    # Base classes
    "DataProvider",
    "DataProviderManager",
    "DataFrequency",
    "DataType",
    "StockInfo",
    "MarketData",
    "standardize_columns",
    "ensure_datetime_index",

    # Cache
    "DataCache",
    "DataFrameCache",
    "CacheKey",
    "cache",
    "df_cache",
    "cached",
    "clear_all_cache",
    "get_cache_stats",

    # Processor
    "DataProcessor",
    "process_data",

    # Provider functions
    "get_qlib_provider",
    "get_tushare_provider",
    "get_akshare_provider",
]