"""
数据层基类模块
Data Layer Base Module

该模块定义了数据提供者的抽象基类，
提供统一的数据访问接口。

This module defines the abstract base class for data providers,
providing a unified data access interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.exceptions import DataSourceError, DataNotFoundError, DataValidationError


class DataFrequency(Enum):
    """
    数据频率枚举
    Data frequency enumeration
    """
    TICK = "tick"           # 逐笔 / Tick data
    MIN1 = "1min"           # 1分钟 / 1 minute
    MIN5 = "5min"           # 5分钟 / 5 minutes
    MIN15 = "15min"         # 15分钟 / 15 minutes
    MIN30 = "30min"         # 30分钟 / 30 minutes
    HOUR = "1hour"          # 1小时 / 1 hour
    DAY = "1d"              # 日线 / Daily
    WEEK = "1w"             # 周线 / Weekly
    MONTH = "1M"            # 月线 / Monthly


class DataType(Enum):
    """
    数据类型枚举
    Data type enumeration
    """
    MARKET = "market"           # 行情数据 / Market data
    FINANCIAL = "financial"     # 财务数据 / Financial data
    FACTOR = "factor"           # 因子数据 / Factor data
    INDEX = "index"             # 指数数据 / Index data
    INDUSTRY = "industry"       # 行业数据 / Industry data


@dataclass
class StockInfo:
    """
    股票信息数据类
    Stock information data class

    Attributes:
        code: 股票代码 / Stock code
        name: 股票名称 / Stock name
        exchange: 交易所 / Exchange
        industry: 行业 / Industry
        list_date: 上市日期 / Listing date
        market_cap: 总市值 / Total market cap
    """
    code: str
    name: str
    exchange: str
    industry: Optional[str] = None
    list_date: Optional[datetime] = None
    market_cap: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "exchange": self.exchange,
            "industry": self.industry,
            "list_date": self.list_date.isoformat() if self.list_date else None,
            "market_cap": self.market_cap
        }


@dataclass
class MarketData:
    """
    行情数据类
    Market data class

    Attributes:
        code: 股票代码 / Stock code
        datetime: 时间 / Datetime
        open: 开盘价 / Open price
        high: 最高价 / High price
        low: 最低价 / Low price
        close: 收盘价 / Close price
        volume: 成交量 / Volume
        amount: 成交额 / Amount
    """
    code: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "datetime": self.datetime.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount
        }


class DataProvider(ABC):
    """
    数据提供者抽象基类
    Abstract base class for data providers

    所有数据提供者必须实现此接口。
    All data providers must implement this interface.

    Attributes:
        name: 数据提供者名称 / Data provider name
        config: 配置字典 / Configuration dictionary
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据提供者

        Args:
            name: 数据提供者名称 / Data provider name
            config: 配置字典 / Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化数据提供者
        Initialize data provider

        建立连接、验证配置等。
        Establish connection, validate configuration, etc.

        Returns:
            是否初始化成功 / Whether initialization succeeded
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查数据提供者是否可用
        Check if data provider is available

        Returns:
            是否可用 / Whether available
        """
        pass

    @abstractmethod
    def get_stock_list(self, market: str = "cn") -> pd.DataFrame:
        """
        获取股票列表
        Get stock list

        Args:
            market: 市场代码 / Market code

        Returns:
            股票列表DataFrame / Stock list DataFrame
            Columns: code, name, exchange, industry, list_date
        """
        pass

    @abstractmethod
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """
        获取股票信息
        Get stock information

        Args:
            code: 股票代码 / Stock code

        Returns:
            股票信息 / Stock information
        """
        pass

    @abstractmethod
    def get_market_data(
        self,
        code: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        frequency: DataFrequency = DataFrequency.DAY,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取行情数据
        Get market data

        Args:
            code: 股票代码 / Stock code
            start_date: 开始日期 / Start date
            end_date: 结束日期 / End date
            frequency: 数据频率 / Data frequency
            fields: 需要的字段 / Required fields

        Returns:
            行情数据DataFrame / Market data DataFrame
            Index: datetime
            Columns: open, high, low, close, volume, amount
        """
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_code: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        frequency: DataFrequency = DataFrequency.DAY
    ) -> pd.DataFrame:
        """
        获取指数数据
        Get index data

        Args:
            index_code: 指数代码 / Index code
            start_date: 开始日期 / Start date
            end_date: 结束日期 / End date
            frequency: 数据频率 / Data frequency

        Returns:
            指数数据DataFrame / Index data DataFrame
        """
        pass

    @abstractmethod
    def get_financial_data(
        self,
        code: str,
        report_type: str = "all",
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取财务数据
        Get financial data

        Args:
            code: 股票代码 / Stock code
            report_type: 报告类型 / Report type
            fields: 需要的字段 / Required fields

        Returns:
            财务数据DataFrame / Financial data DataFrame
        """
        pass

    @abstractmethod
    def get_trading_calendar(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        market: str = "cn"
    ) -> List[datetime]:
        """
        获取交易日历
        Get trading calendar

        Args:
            start_date: 开始日期 / Start date
            end_date: 结束日期 / End date
            market: 市场代码 / Market code

        Returns:
            交易日列表 / Trading days list
        """
        pass

    def get_latest_price(self, code: str) -> Optional[float]:
        """
        获取最新价格
        Get latest price

        Args:
            code: 股票代码 / Stock code

        Returns:
            最新价格 / Latest price
        """
        try:
            # 获取最近一天的收盘价
            end_date = datetime.now()
            start_date = end_date - pd.Timedelta(days=7)  # 最近7天

            data = self.get_market_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency=DataFrequency.DAY
            )

            if not data.empty:
                return data["close"].iloc[-1]
            return None
        except Exception as e:
            raise DataSourceError(
                source=self.name,
                message=f"获取最新价格失败: {code}",
                details=str(e)
            )

    def validate_data(
        self,
        data: pd.DataFrame,
        required_columns: Optional[List[str]] = None
    ) -> bool:
        """
        验证数据
        Validate data

        检查数据是否包含必要的列，是否有有效值。

        Args:
            data: 待验证的数据 / Data to validate
            required_columns: 必需的列 / Required columns

        Returns:
            是否验证通过 / Whether validation passed

        Raises:
            DataValidationError: 数据验证失败
        """
        if data is None or data.empty:
            raise DataValidationError(
                message="数据为空",
                details="DataFrame is None or empty"
            )

        # 默认必需列 / Default required columns
        if required_columns is None:
            required_columns = ["open", "high", "low", "close", "volume"]

        # 检查必需列是否存在
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise DataValidationError(
                message=f"缺少必需的列: {missing_columns}",
                details=f"Available columns: {list(data.columns)}"
            )

        # 检查是否有有效数据
        if data[required_columns].isna().all().all():
            raise DataValidationError(
                message="数据全部为空值",
                details="All values are NaN"
            )

        return True

    def _ensure_initialized(self):
        """
        确保数据提供者已初始化
        Ensure data provider is initialized
        """
        if not self._initialized:
            success = self.initialize()
            if not success:
                raise DataSourceError(
                    source=self.name,
                    message="数据提供者初始化失败"
                )


class DataProviderManager:
    """
    数据提供者管理器
    Data provider manager

    管理多个数据提供者，提供统一的数据访问接口。
    Manage multiple data providers, providing unified data access interface.

    根据优先级选择可用的数据提供者。
    Select available data providers based on priority.
    """

    def __init__(self):
        """初始化管理器"""
        self._providers: Dict[str, DataProvider] = {}
        self._priority: Dict[str, int] = {}

    def register(self, provider: DataProvider, priority: int = 1):
        """
        注册数据提供者
        Register data provider

        Args:
            provider: 数据提供者实例 / Data provider instance
            priority: 优先级（数值越小优先级越高）/ Priority (lower value means higher priority)
        """
        self._providers[provider.name] = provider
        self._priority[provider.name] = priority

    def unregister(self, name: str):
        """
        注销数据提供者
        Unregister data provider

        Args:
            name: 数据提供者名称 / Data provider name
        """
        if name in self._providers:
            del self._providers[name]
            del self._priority[name]

    def get_provider(self, name: Optional[str] = None) -> Optional[DataProvider]:
        """
        获取数据提供者
        Get data provider

        Args:
            name: 指定的数据提供者名称，如果为None则返回优先级最高的可用提供者

        Returns:
            数据提供者实例 / Data provider instance
        """
        if name:
            return self._providers.get(name)

        # 返回优先级最高的可用提供者
        sorted_providers = sorted(
            self._priority.keys(),
            key=lambda x: self._priority[x]
        )

        for provider_name in sorted_providers:
            provider = self._providers[provider_name]
            if provider.is_available():
                return provider

        return None

    def get_all_providers(self) -> Dict[str, DataProvider]:
        """
        获取所有数据提供者
        Get all data providers

        Returns:
            数据提供者字典 / Dictionary of data providers
        """
        return self._providers.copy()

    def initialize_all(self) -> Dict[str, bool]:
        """
        初始化所有数据提供者
        Initialize all data providers

        Returns:
            初始化结果字典 / Dictionary of initialization results
        """
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = provider.initialize()
            except Exception as e:
                results[name] = False
        return results


# ==================== 辅助函数 / Helper Functions ====================

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化列名
    Standardize column names

    将不同的列名命名风格统一为小写下划线格式。
    Unify different column naming styles to lowercase underscore format.

    Args:
        df: 原始DataFrame / Original DataFrame

    Returns:
        标准化后的DataFrame / Standardized DataFrame
    """
    column_mapping = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Amount": "amount",
        "Adj Close": "adj_close",
        "日期": "datetime",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
        "涨跌幅": "pct_change",
        "涨跌额": "change",
        "换手率": "turnover",
    }

    df = df.copy()
    df.columns = [column_mapping.get(col, col.lower().replace(" ", "_")) for col in df.columns]

    return df


def ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    确保DataFrame具有日期时间索引
    Ensure DataFrame has datetime index

    Args:
        df: 原始DataFrame / Original DataFrame

    Returns:
        具有日期时间索引的DataFrame / DataFrame with datetime index
    """
    df = df.copy()

    # 如果索引已经是日期时间类型，直接返回
    if isinstance(df.index, pd.DatetimeIndex):
        return df

    # 尝试从索引转换
    try:
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        pass

    # 尝试从列转换
    for col in ["datetime", "date", "日期", "time", "trade_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            df = df.set_index(col)
            return df

    return df