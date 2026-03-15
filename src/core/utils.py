"""
工具函数模块
Utility Functions Module

该模块提供应用程序中常用的工具函数，
包括日志配置、数据转换、日期处理等。

This module provides common utility functions for the application,
including logging configuration, data conversion, date processing, etc.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import time

import pandas as pd
import numpy as np
from loguru import logger

# 添加项目根目录到路径 / Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import LOG_CONFIG, PROJECT_ROOT


# ==================== 日志配置 / Logging Configuration ====================

def setup_logger():
    """
    配置日志系统
    Configure logging system

    使用 loguru 配置日志输出到控制台和文件。
    Configure loguru to output logs to console and file.
    """
    # 移除默认处理器 / Remove default handler
    logger.remove()

    # 添加控制台处理器 / Add console handler
    logger.add(
        sys.stderr,
        format=LOG_CONFIG.format,
        level=LOG_CONFIG.level,
        colorize=True
    )

    # 添加文件处理器 / Add file handler
    logger.add(
        LOG_CONFIG.file,
        format=LOG_CONFIG.format,
        level=LOG_CONFIG.level,
        rotation=LOG_CONFIG.rotation,
        retention=LOG_CONFIG.retention,
        encoding="utf-8"
    )

    return logger


# 初始化日志 / Initialize logger
logger = setup_logger()


# ==================== 装饰器 / Decorators ====================

def timer(func: Callable) -> Callable:
    """
    计时装饰器
    Timer decorator

    用于测量函数执行时间。
    Used to measure function execution time.

    Args:
        func: 被装饰的函数 / Decorated function

    Returns:
        装饰后的函数 / Decorated function

    Example:
        @timer
        def slow_function():
            time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} 执行时间: {end_time - start_time:.4f} 秒")
        return result
    return wrapper


def retry(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器
    Retry decorator

    当函数抛出指定异常时自动重试。
    Automatically retry when function raises specified exceptions.

    Args:
        max_retries: 最大重试次数 / Maximum retry count
        delay: 重试延迟（秒） / Retry delay in seconds
        exceptions: 需要重试的异常类型 / Exception types to retry

    Returns:
        装饰器 / Decorator

    Example:
        @retry(max_retries=3, delay=1.0)
        def unstable_function():
            # 可能失败的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 执行失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} 执行失败，已达到最大重试次数: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    执行日志装饰器
    Execution logging decorator

    记录函数的开始、结束和异常。
    Log function start, end, and exceptions.

    Args:
        func: 被装饰的函数 / Decorated function

    Returns:
        装饰后的函数 / Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"开始执行: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"执行完成: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"执行失败: {func.__name__}, 错误: {e}")
            raise
    return wrapper


# ==================== 日期处理工具 / Date Processing Utilities ====================

def parse_date(date_str: Union[str, datetime, pd.Timestamp]) -> datetime:
    """
    解析日期字符串
    Parse date string

    支持多种日期格式：
    Supports multiple date formats:
    - "YYYY-MM-DD"
    - "YYYY/MM/DD"
    - "YYYYMMDD"
    - datetime 对象
    - pandas Timestamp 对象

    Args:
        date_str: 日期字符串或对象 / Date string or object

    Returns:
        datetime 对象 / datetime object

    Raises:
        ValueError: 日期格式无效 / Invalid date format
    """
    if isinstance(date_str, datetime):
        return date_str
    if isinstance(date_str, pd.Timestamp):
        return date_str.to_pydatetime()

    # 尝试多种格式 / Try multiple formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue

    raise ValueError(f"无法解析日期: {date_str}")


def get_trading_days(start_date: Union[str, datetime],
                     end_date: Union[str, datetime],
                     market: str = "cn") -> List[datetime]:
    """
    获取交易日列表
    Get list of trading days

    获取指定日期范围内的交易日（排除周末和节假日）。
    Get trading days within the specified date range (excluding weekends and holidays).

    Args:
        start_date: 开始日期 / Start date
        end_date: 结束日期 / End date
        market: 市场（目前仅支持 cn）/ Market (currently only cn supported)

    Returns:
        交易日列表 / List of trading days

    Note:
        此函数使用简单的工作日过滤，实际交易日需要考虑节假日。
        使用 qlib 或其他数据源获取精确的交易日。
        This function uses simple weekday filtering, actual trading days need to consider holidays.
        Use qlib or other data sources for precise trading days.
    """
    start = parse_date(start_date)
    end = parse_date(end_date)

    # 简单实现：排除周末 / Simple implementation: exclude weekends
    trading_days = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # 周一到周五 / Monday to Friday
            trading_days.append(current)
        current += timedelta(days=1)

    return trading_days


def date_range_to_str(start_date: Union[str, datetime],
                      end_date: Union[str, datetime]) -> str:
    """
    将日期范围转换为字符串
    Convert date range to string

    Args:
        start_date: 开始日期 / Start date
        end_date: 结束日期 / End date

    Returns:
        日期范围字符串 / Date range string
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    return f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"


# ==================== 数据处理工具 / Data Processing Utilities ====================

def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码
    Normalize stock code

    将股票代码转换为标准格式（如：000001.SZ）。
    Convert stock code to standard format (e.g., 000001.SZ).

    Args:
        code: 股票代码 / Stock code

    Returns:
        标准化后的股票代码 / Normalized stock code

    Examples:
        >>> normalize_stock_code("000001")
        "000001.SZ"
        >>> normalize_stock_code("600000")
        "600000.SH"
        >>> normalize_stock_code("000001.SZ")
        "000001.SZ"
    """
    code = code.strip().upper()

    # 如果已经有后缀，直接返回 / If already has suffix, return directly
    if "." in code:
        return code

    # 根据股票代码规则添加后缀 / Add suffix based on stock code rules
    if code.startswith("6"):
        return f"{code}.SH"  # 上海证券交易所 / Shanghai Stock Exchange
    elif code.startswith(("0", "3")):
        return f"{code}.SZ"  # 深圳证券交易所 / Shenzhen Stock Exchange
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"  # 北京证券交易所 / Beijing Stock Exchange
    else:
        return f"{code}.SZ"  # 默认深圳 / Default Shenzhen


def safe_divide(a: Union[pd.Series, np.ndarray, float],
                b: Union[pd.Series, np.ndarray, float],
                fill_value: float = 0.0) -> Union[pd.Series, np.ndarray, float]:
    """
    安全除法
    Safe division

    避免除零错误，当除数为0时返回填充值。
    Avoid division by zero error, return fill value when divisor is 0.

    Args:
        a: 被除数 / Dividend
        b: 除数 / Divisor
        fill_value: 填充值 / Fill value

    Returns:
        除法结果 / Division result
    """
    if isinstance(a, pd.Series) or isinstance(b, pd.Series):
        a = pd.Series(a) if not isinstance(a, pd.Series) else a
        b = pd.Series(b) if not isinstance(b, pd.Series) else b
        result = a / b.replace(0, np.nan)
        return result.fillna(fill_value)
    elif isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        a = np.array(a)
        b = np.array(b)
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.where(b != 0, a / b, fill_value)
        return result
    else:
        return a / b if b != 0 else fill_value


def calculate_returns(prices: pd.Series,
                      method: str = "simple") -> pd.Series:
    """
    计算收益率
    Calculate returns

    Args:
        prices: 价格序列 / Price series
        method: 计算方法 ("simple" 或 "log") / Calculation method ("simple" or "log")

    Returns:
        收益率序列 / Returns series
    """
    if method == "log":
        return np.log(prices / prices.shift(1))
    else:
        return prices.pct_change()


def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    计算累计收益率
    Calculate cumulative returns

    Args:
        returns: 收益率序列 / Returns series

    Returns:
        累计收益率序列 / Cumulative returns series
    """
    return (1 + returns).cumprod() - 1


def resample_data(df: pd.DataFrame,
                  freq: str = "D",
                  agg_dict: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    重采样数据
    Resample data

    将高频数据聚合为低频数据。
    Aggregate high-frequency data to low-frequency data.

    Args:
        df: DataFrame，索引为日期时间 / DataFrame with datetime index
        freq: 重采样频率 (D: 日, W: 周, M: 月) / Resample frequency (D: daily, W: weekly, M: monthly)
        agg_dict: 聚合规则字典 / Aggregation rules dictionary

    Returns:
        重采样后的DataFrame / Resampled DataFrame
    """
    if agg_dict is None:
        agg_dict = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }

    # 确保索引为日期时间 / Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    return df.resample(freq).agg(agg_dict)


# ==================== 格式化工具 / Formatting Utilities ====================

def format_number(value: Union[int, float],
                  decimal: int = 2,
                  thousands_sep: bool = True) -> str:
    """
    格式化数字
    Format number

    Args:
        value: 数值 / Value
        decimal: 小数位数 / Decimal places
        thousands_sep: 是否使用千位分隔符 / Whether to use thousands separator

    Returns:
        格式化后的字符串 / Formatted string
    """
    if thousands_sep:
        return f"{value:,.{decimal}f}"
    else:
        return f"{value:.{decimal}f}"


def format_percentage(value: float, decimal: int = 2) -> str:
    """
    格式化百分比
    Format percentage

    Args:
        value: 数值（如0.05表示5%）/ Value (e.g., 0.05 means 5%)
        decimal: 小数位数 / Decimal places

    Returns:
        格式化后的百分比字符串 / Formatted percentage string
    """
    return f"{value * 100:.{decimal}f}%"


def format_money(value: float, currency: str = "¥") -> str:
    """
    格式化金额
    Format money

    Args:
        value: 金额 / Amount
        currency: 货币符号 / Currency symbol

    Returns:
        格式化后的金额字符串 / Formatted money string
    """
    if abs(value) >= 1e8:  # 亿 / 100 million
        return f"{currency}{value / 1e8:.2f}亿"
    elif abs(value) >= 1e4:  # 万 / 10 thousand
        return f"{currency}{value / 1e4:.2f}万"
    else:
        return f"{currency}{value:,.2f}"


def format_volume(value: Union[int, float]) -> str:
    """
    格式化成交量
    Format volume

    Args:
        value: 成交量 / Volume

    Returns:
        格式化后的成交量字符串 / Formatted volume string
    """
    if value >= 1e8:  # 亿股 / 100 million shares
        return f"{value / 1e8:.2f}亿"
    elif value >= 1e4:  # 万股 / 10 thousand shares
        return f"{value / 1e4:.2f}万"
    else:
        return f"{value:,.0f}"


# ==================== 验证工具 / Validation Utilities ====================

def validate_stock_code(code: str) -> bool:
    """
    验证股票代码格式
    Validate stock code format

    Args:
        code: 股票代码 / Stock code

    Returns:
        是否有效 / Whether valid
    """
    code = code.strip().upper()

    # 检查格式：6位数字或带后缀的格式
    # Check format: 6 digits or format with suffix
    import re

    # 匹配纯数字代码 / Match pure numeric code
    if re.match(r"^\d{6}$", code):
        return True

    # 匹配带后缀的代码 / Match code with suffix
    if re.match(r"^\d{6}\.(SH|SZ|BJ)$", code):
        return True

    return False


def validate_date_range(start_date: Union[str, datetime],
                        end_date: Union[str, datetime]) -> bool:
    """
    验证日期范围
    Validate date range

    Args:
        start_date: 开始日期 / Start date
        end_date: 结束日期 / End date

    Returns:
        是否有效 / Whether valid
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return start <= end
    except ValueError:
        return False


# ==================== 文件工具 / File Utilities ====================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在
    Ensure directory exists

    Args:
        path: 目录路径 / Directory path

    Returns:
        目录路径 / Directory path
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载JSON文件
    Load JSON file

    Args:
        file_path: 文件路径 / File path

    Returns:
        JSON数据 / JSON data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2):
    """
    保存JSON文件
    Save JSON file

    Args:
        data: 要保存的数据 / Data to save
        file_path: 文件路径 / File path
        indent: 缩进空格数 / Indent spaces
    """
    ensure_dir(Path(file_path).parent)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


# ==================== 初始化包 / Initialize Package ====================

# 创建 __init__.py 文件内容
__all__ = [
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