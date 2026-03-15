"""
自定义异常模块
Custom Exceptions Module

该模块定义了应用程序中使用的所有自定义异常类，
提供清晰的错误处理和错误信息。

This module defines all custom exception classes used in the application,
providing clear error handling and error messages.
"""

from typing import Optional, Any


class StockAnalysisError(Exception):
    """
    股票分析基础异常类
    Base exception class for stock analysis

    所有自定义异常的基类，提供统一的错误处理接口。
    Base class for all custom exceptions, providing unified error handling interface.

    Attributes:
        message: 错误信息 / Error message
        code: 错误代码 / Error code
        details: 错误详情 / Error details
    """

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        """
        初始化异常

        Args:
            message: 错误信息 / Error message
            code: 错误代码（可选）/ Error code (optional)
            details: 错误详情（可选）/ Error details (optional)
        """
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        """返回异常的字符串表示"""
        if self.details:
            return f"[{self.code}] {self.message} - Details: {self.details}"
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict:
        """
        将异常转换为字典格式
        Convert exception to dictionary format

        Returns:
            包含错误信息的字典 / Dictionary containing error information
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# ==================== 数据相关异常 / Data Related Exceptions ====================

class DataError(StockAnalysisError):
    """
    数据错误基类
    Base class for data errors
    """
    pass


class DataSourceError(DataError):
    """
    数据源错误
    Data source error

    当数据源不可用或配置错误时抛出。
    Raised when data source is unavailable or misconfigured.
    """

    def __init__(self, source: str, message: str = None, details: Optional[Any] = None):
        """
        初始化数据源错误

        Args:
            source: 数据源名称 / Data source name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"数据源 '{source}' 错误"
        super().__init__(message, code="DATA_SOURCE_ERROR", details=details)
        self.source = source


class DataNotFoundError(DataError):
    """
    数据未找到错误
    Data not found error

    当请求的数据不存在时抛出。
    Raised when requested data does not exist.
    """

    def __init__(self, data_type: str, identifier: str, details: Optional[Any] = None):
        """
        初始化数据未找到错误

        Args:
            data_type: 数据类型 / Data type
            identifier: 数据标识符 / Data identifier
            details: 错误详情 / Error details
        """
        message = f"未找到{data_type}数据: {identifier}"
        super().__init__(message, code="DATA_NOT_FOUND", details=details)
        self.data_type = data_type
        self.identifier = identifier


class DataValidationError(DataError):
    """
    数据验证错误
    Data validation error

    当数据验证失败时抛出。
    Raised when data validation fails.
    """

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Any] = None):
        """
        初始化数据验证错误

        Args:
            message: 错误信息 / Error message
            field: 字段名称 / Field name
            details: 错误详情 / Error details
        """
        code = "DATA_VALIDATION_ERROR"
        if field:
            message = f"字段 '{field}' 验证失败: {message}"
        super().__init__(message, code=code, details=details)
        self.field = field


class DataCacheError(DataError):
    """
    数据缓存错误
    Data cache error

    当缓存操作失败时抛出。
    Raised when cache operation fails.
    """

    def __init__(self, operation: str, message: str = None, details: Optional[Any] = None):
        """
        初始化缓存错误

        Args:
            operation: 操作类型 / Operation type
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"缓存操作 '{operation}' 失败"
        super().__init__(message, code="CACHE_ERROR", details=details)
        self.operation = operation


# ==================== 模型相关异常 / Model Related Exceptions ====================

class ModelError(StockAnalysisError):
    """
    模型错误基类
    Base class for model errors
    """
    pass


class ModelNotFoundError(ModelError):
    """
    模型未找到错误
    Model not found error

    当请求的模型不存在时抛出。
    Raised when requested model does not exist.
    """

    def __init__(self, model_name: str, details: Optional[Any] = None):
        """
        初始化模型未找到错误

        Args:
            model_name: 模型名称 / Model name
            details: 错误详情 / Error details
        """
        message = f"未找到模型: {model_name}"
        super().__init__(message, code="MODEL_NOT_FOUND", details=details)
        self.model_name = model_name


class ModelTrainingError(ModelError):
    """
    模型训练错误
    Model training error

    当模型训练失败时抛出。
    Raised when model training fails.
    """

    def __init__(self, model_name: str, message: str = None, details: Optional[Any] = None):
        """
        初始化模型训练错误

        Args:
            model_name: 模型名称 / Model name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"模型 '{model_name}' 训练失败"
        super().__init__(message, code="MODEL_TRAINING_ERROR", details=details)
        self.model_name = model_name


class ModelPredictionError(ModelError):
    """
    模型预测错误
    Model prediction error

    当模型预测失败时抛出。
    Raised when model prediction fails.
    """

    def __init__(self, model_name: str, message: str = None, details: Optional[Any] = None):
        """
        初始化模型预测错误

        Args:
            model_name: 模型名称 / Model name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"模型 '{model_name}' 预测失败"
        super().__init__(message, code="MODEL_PREDICTION_ERROR", details=details)
        self.model_name = model_name


# ==================== 分析相关异常 / Analysis Related Exceptions ====================

class AnalysisError(StockAnalysisError):
    """
    分析错误基类
    Base class for analysis errors
    """
    pass


class TechnicalAnalysisError(AnalysisError):
    """
    技术分析错误
    Technical analysis error

    当技术分析计算失败时抛出。
    Raised when technical analysis calculation fails.
    """

    def __init__(self, indicator: str, message: str = None, details: Optional[Any] = None):
        """
        初始化技术分析错误

        Args:
            indicator: 指标名称 / Indicator name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"技术指标 '{indicator}' 计算失败"
        super().__init__(message, code="TECHNICAL_ANALYSIS_ERROR", details=details)
        self.indicator = indicator


class FactorAnalysisError(AnalysisError):
    """
    因子分析错误
    Factor analysis error

    当因子分析失败时抛出。
    Raised when factor analysis fails.
    """

    def __init__(self, factor: str, message: str = None, details: Optional[Any] = None):
        """
        初始化因子分析错误

        Args:
            factor: 因子名称 / Factor name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"因子 '{factor}' 分析失败"
        super().__init__(message, code="FACTOR_ANALYSIS_ERROR", details=details)
        self.factor = factor


class BacktestError(AnalysisError):
    """
    回测错误
    Backtest error

    当回测执行失败时抛出。
    Raised when backtest execution fails.
    """

    def __init__(self, strategy: str, message: str = None, details: Optional[Any] = None):
        """
        初始化回测错误

        Args:
            strategy: 策略名称 / Strategy name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = message or f"策略 '{strategy}' 回测失败"
        super().__init__(message, code="BACKTEST_ERROR", details=details)
        self.strategy = strategy


# ==================== 交易相关异常 / Trading Related Exceptions ====================

class TradingError(StockAnalysisError):
    """
    交易错误基类
    Base class for trading errors
    """
    pass


class InsufficientFundsError(TradingError):
    """
    资金不足错误
    Insufficient funds error

    当账户资金不足以执行交易时抛出。
    Raised when account has insufficient funds for trading.
    """

    def __init__(self, required: float, available: float, details: Optional[Any] = None):
        """
        初始化资金不足错误

        Args:
            required: 所需资金 / Required funds
            available: 可用资金 / Available funds
            details: 错误详情 / Error details
        """
        message = f"资金不足: 需要 {required:,.2f}, 可用 {available:,.2f}"
        super().__init__(message, code="INSUFFICIENT_FUNDS", details=details)
        self.required = required
        self.available = available


class InsufficientSharesError(TradingError):
    """
    股份不足错误
    Insufficient shares error

    当持仓股份不足以卖出时抛出。
    Raised when position has insufficient shares for selling.
    """

    def __init__(self, stock: str, required: int, available: int, details: Optional[Any] = None):
        """
        初始化股份不足错误

        Args:
            stock: 股票代码 / Stock code
            required: 所需股数 / Required shares
            available: 可用股数 / Available shares
            details: 错误详情 / Error details
        """
        message = f"股票 {stock} 持仓不足: 需要 {required}, 可用 {available}"
        super().__init__(message, code="INSUFFICIENT_SHARES", details=details)
        self.stock = stock
        self.required = required
        self.available = available


class OrderError(TradingError):
    """
    订单错误
    Order error

    当订单操作失败时抛出。
    Raised when order operation fails.
    """

    def __init__(self, order_id: str, message: str, details: Optional[Any] = None):
        """
        初始化订单错误

        Args:
            order_id: 订单ID / Order ID
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        super().__init__(message, code="ORDER_ERROR", details=details)
        self.order_id = order_id


class PositionError(TradingError):
    """
    持仓错误
    Position error

    当持仓操作失败时抛出。
    Raised when position operation fails.
    """

    def __init__(self, stock: str, message: str, details: Optional[Any] = None):
        """
        初始化持仓错误

        Args:
            stock: 股票代码 / Stock code
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        super().__init__(message, code="POSITION_ERROR", details=details)
        self.stock = stock


# ==================== 配置相关异常 / Configuration Related Exceptions ====================

class ConfigurationError(StockAnalysisError):
    """
    配置错误基类
    Base class for configuration errors
    """
    pass


class ConfigNotFoundError(ConfigurationError):
    """
    配置未找到错误
    Configuration not found error

    当配置文件不存在时抛出。
    Raised when configuration file does not exist.
    """

    def __init__(self, config_name: str, details: Optional[Any] = None):
        """
        初始化配置未找到错误

        Args:
            config_name: 配置名称 / Configuration name
            details: 错误详情 / Error details
        """
        message = f"未找到配置: {config_name}"
        super().__init__(message, code="CONFIG_NOT_FOUND", details=details)
        self.config_name = config_name


class ConfigValidationError(ConfigurationError):
    """
    配置验证错误
    Configuration validation error

    当配置验证失败时抛出。
    Raised when configuration validation fails.
    """

    def __init__(self, config_name: str, message: str, details: Optional[Any] = None):
        """
        初始化配置验证错误

        Args:
            config_name: 配置名称 / Configuration name
            message: 错误信息 / Error message
            details: 错误详情 / Error details
        """
        message = f"配置 '{config_name}' 验证失败: {message}"
        super().__init__(message, code="CONFIG_VALIDATION_ERROR", details=details)
        self.config_name = config_name


# ==================== 工具函数 / Utility Functions ====================

def handle_exception(e: Exception, raise_as: type = None) -> StockAnalysisError:
    """
    异常处理工具函数
    Exception handling utility function

    将普通异常转换为自定义异常。
    Convert regular exceptions to custom exceptions.

    Args:
        e: 原始异常 / Original exception
        raise_as: 目标异常类型 / Target exception type

    Returns:
        转换后的异常 / Converted exception
    """
    if isinstance(e, StockAnalysisError):
        return e

    if raise_as:
        return raise_as(str(e), details={"original_exception": type(e).__name__})

    return StockAnalysisError(str(e), code="INTERNAL_ERROR", details={"original_exception": type(e).__name__})