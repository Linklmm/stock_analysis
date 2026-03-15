"""
qlib 数据提供者模块
qlib Data Provider Module

该模块实现了基于微软 qlib 的数据提供者，
提供A股市场数据访问接口。

This module implements data provider based on Microsoft qlib,
providing A-share market data access interface.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import warnings

import pandas as pd
import numpy as np

from src.data.base import (
    DataProvider,
    DataFrequency,
    DataType,
    StockInfo,
    standardize_columns,
    ensure_datetime_index
)
from src.core.exceptions import DataSourceError, DataNotFoundError
from src.core.utils import logger, parse_date, normalize_stock_code
from config.settings import QLIB_DATA_DIR, get_data_source_config


class QlibDataProvider(DataProvider):
    """
    qlib 数据提供者
    qlib data provider

    使用微软 qlib 框架获取A股市场数据。
    Use Microsoft qlib framework to get A-share market data.

    qlib 是微软开源的AI量化投资平台，提供丰富的中国市场数据。
    qlib is Microsoft's open-source AI quantitative investment platform,
    providing rich Chinese market data.

    Attributes:
        provider_uri: qlib 数据路径 / qlib data path
        region: 地区设置 / Region setting
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 qlib 数据提供者

        Args:
            config: 配置字典 / Configuration dictionary
                - provider_uri: qlib 数据路径 / qlib data path
                - region: 地区设置 / Region setting (默认 "cn")
                - redis_host: Redis 主机 (可选) / Redis host (optional)
                - redis_port: Redis 端口 (可选) / Redis port (optional)
        """
        super().__init__(name="qlib", config=config)

        # 从配置获取参数 / Get parameters from config
        self.provider_uri = self.config.get("provider_uri", str(QLIB_DATA_DIR))
        self.region = self.config.get("region", "cn")
        self.redis_host = self.config.get("redis_host")
        self.redis_port = self.config.get("redis_port", 6379)

        # qlib 相关对象 / qlib related objects
        self._qlib = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        初始化 qlib
        Initialize qlib

        加载 qlib 并初始化数据配置。
        Load qlib and initialize data configuration.

        Returns:
            是否初始化成功 / Whether initialization succeeded
        """
        try:
            import qlib
            from qlib.config import REG_CN

            # 检查是否已经初始化 / Check if already initialized
            if qlib.get_data_provider() is not None:
                logger.info("qlib 已经初始化")
                self._initialized = True
                self._qlib = qlib
                return True

            # 初始化 qlib / Initialize qlib
            qlib.init(
                provider_uri=self.provider_uri,
                region=self.region,
                redis_host=self.redis_host,
                redis_port=self.redis_port
            )

            self._qlib = qlib
            self._initialized = True
            logger.info(f"qlib 初始化成功，数据路径: {self.provider_uri}")
            return True

        except ImportError:
            logger.error("qlib 未安装，请运行: pip install pyqlib")
            return False
        except Exception as e:
            logger.error(f"qlib 初始化失败: {e}")
            self._initialized = False
            return False

    def is_available(self) -> bool:
        """
        检查 qlib 是否可用
        Check if qlib is available

        Returns:
            是否可用 / Whether available
        """
        if not self._initialized:
            return False

        try:
            import qlib
            return qlib.get_data_provider() is not None
        except Exception:
            return False

    def get_stock_list(self, market: str = "cn") -> pd.DataFrame:
        """
        获取股票列表
        Get stock list

        使用 qlib 获取A股股票列表。
        Use qlib to get A-share stock list.

        Args:
            market: 市场代码 (默认 "cn") / Market code (default "cn")

        Returns:
            股票列表DataFrame / Stock list DataFrame
            Columns: code, name, exchange, industry, list_date
        """
        self._ensure_initialized()

        try:
            from qlib.data import D

            # 获取所有股票代码 / Get all stock codes
            instruments = D.instruments(market=market)

            if instruments is None or instruments.empty:
                logger.warning("未获取到股票列表")
                return pd.DataFrame()

            # 转换为标准格式 / Convert to standard format
            result = []
            for inst in instruments:
                try:
                    info = D.instrument(inst)
                    result.append({
                        "code": inst,
                        "name": info.get("name", inst) if isinstance(info, dict) else inst,
                        "exchange": self._get_exchange(inst),
                        "industry": info.get("industry") if isinstance(info, dict) else None,
                        "list_date": info.get("list_date") if isinstance(info, dict) else None
                    })
                except Exception as e:
                    logger.debug(f"获取股票 {inst} 信息失败: {e}")
                    result.append({
                        "code": inst,
                        "name": inst,
                        "exchange": self._get_exchange(inst),
                        "industry": None,
                        "list_date": None
                    })

            return pd.DataFrame(result)

        except Exception as e:
            raise DataSourceError(
                source=self.name,
                message="获取股票列表失败",
                details=str(e)
            )

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """
        获取股票信息
        Get stock information

        Args:
            code: 股票代码 / Stock code

        Returns:
            股票信息 / Stock information
        """
        self._ensure_initialized()

        try:
            from qlib.data import D

            # 标准化股票代码 / Normalize stock code
            code = normalize_stock_code(code)
            # qlib 使用不带后缀的格式 / qlib uses format without suffix
            qlib_code = code.split(".")[0]

            info = D.instrument(qlib_code)

            if info is None:
                return None

            return StockInfo(
                code=code,
                name=info.get("name", code) if isinstance(info, dict) else code,
                exchange=self._get_exchange(code),
                industry=info.get("industry") if isinstance(info, dict) else None,
                list_date=parse_date(info["list_date"]) if isinstance(info, dict) and "list_date" in info else None
            )

        except Exception as e:
            logger.error(f"获取股票信息失败: {code}, {e}")
            return None

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

        使用 qlib 获取股票行情数据。
        Use qlib to get stock market data.

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
        self._ensure_initialized()

        try:
            from qlib.data import D
            from qlib.data.dataset.utils import convert_index

            # 标准化参数 / Normalize parameters
            code = normalize_stock_code(code)
            qlib_code = code.split(".")[0]  # qlib 使用纯数字代码

            start = parse_date(start_date)
            end = parse_date(end_date)

            # 默认字段 / Default fields
            if fields is None:
                fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]

            # qlib 使用 $ 前缀表示特征 / qlib uses $ prefix for features
            qlib_fields = [f if f.startswith("$") else f"${f}" for f in fields]

            # 获取数据 / Get data
            data = D.features(
                instruments=[qlib_code],
                fields=qlib_fields,
                start_time=start.strftime("%Y-%m-%d"),
                end_time=end.strftime("%Y-%m-%d"),
                freq=frequency.value
            )

            if data is None or data.empty:
                logger.warning(f"未获取到股票 {code} 的行情数据")
                return pd.DataFrame()

            # 处理多级索引 / Handle multi-level index
            if isinstance(data.index, pd.MultiIndex):
                data = data.droplevel(0)

            # 重命名列 / Rename columns
            column_mapping = {
                "$open": "open",
                "$close": "close",
                "$high": "high",
                "$low": "low",
                "$volume": "volume",
                "$factor": "factor",
                "$amount": "amount"
            }
            data = data.rename(columns={k: v for k, v in column_mapping.items() if k in data.columns})

            # 计算复权价格 / Calculate adjusted prices
            if "factor" in data.columns and "close" in data.columns:
                factor = data["factor"].fillna(method="ffill")
                for col in ["open", "high", "low", "close"]:
                    if col in data.columns:
                        data[f"{col}"] = data[col] * factor

            # 确保索引为日期时间 / Ensure index is datetime
            data = ensure_datetime_index(data)

            # 添加代码列 / Add code column
            data["code"] = code

            return data

        except Exception as e:
            raise DataSourceError(
                source=self.name,
                message=f"获取行情数据失败: {code}",
                details=str(e)
            )

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

        使用 qlib 获取指数行情数据。
        Use qlib to get index market data.

        Args:
            index_code: 指数代码 / Index code
            start_date: 开始日期 / Start date
            end_date: 结束日期 / End date
            frequency: 数据频率 / Data frequency

        Returns:
            指数数据DataFrame / Index data DataFrame
        """
        self._ensure_initialized()

        try:
            from qlib.data import D

            # qlib 指数代码格式 / qlib index code format
            qlib_index = index_code.replace(".", "").lower()
            if not qlib_index.startswith("sh") and not qlib_index.startswith("sz"):
                qlib_index = f"sh{index_code}" if index_code.startswith("0") else f"sh{index_code}"

            start = parse_date(start_date)
            end = parse_date(end_date)

            fields = ["$open", "$close", "$high", "$low", "$volume"]

            data = D.features(
                instruments=[qlib_index],
                fields=fields,
                start_time=start.strftime("%Y-%m-%d"),
                end_time=end.strftime("%Y-%m-%d"),
                freq=frequency.value
            )

            if data is None or data.empty:
                logger.warning(f"未获取到指数 {index_code} 的数据")
                return pd.DataFrame()

            # 处理多级索引
            if isinstance(data.index, pd.MultiIndex):
                data = data.droplevel(0)

            # 重命名列
            column_mapping = {
                "$open": "open",
                "$close": "close",
                "$high": "high",
                "$low": "low",
                "$volume": "volume"
            }
            data = data.rename(columns={k: v for k, v in column_mapping.items() if k in data.columns})

            data = ensure_datetime_index(data)
            data["code"] = index_code

            return data

        except Exception as e:
            raise DataSourceError(
                source=self.name,
                message=f"获取指数数据失败: {index_code}",
                details=str(e)
            )

    def get_financial_data(
        self,
        code: str,
        report_type: str = "all",
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取财务数据
        Get financial data

        qlib 基础版不直接提供财务数据，需要使用扩展数据。
        qlib basic version doesn't directly provide financial data,
        need to use extended data.

        Args:
            code: 股票代码 / Stock code
            report_type: 报告类型 / Report type
            fields: 需要的字段 / Required fields

        Returns:
            财务数据DataFrame / Financial data DataFrame
        """
        self._ensure_initialized()

        # qlib 基础版财务数据支持有限
        # 建议使用 Tushare 或 AkShare 获取详细财务数据
        logger.warning("qlib 基础版财务数据支持有限，建议使用 Tushare 或 AkShare 数据源")

        try:
            from qlib.data import D

            code = normalize_stock_code(code)
            qlib_code = code.split(".")[0]

            # 尝试获取一些基础财务特征
            financial_fields = [
                "$pe", "$pb", "$ps", "$pcf",
                "$roe", "$roa", "$debt_ratio",
                "$gross_margin", "$net_margin"
            ]

            if fields:
                financial_fields = [f if f.startswith("$") else f"${f}" for f in fields]

            data = D.features(
                instruments=[qlib_code],
                fields=financial_fields,
                start_time="2010-01-01",
                end_time=datetime.now().strftime("%Y-%m-%d"),
                freq="1d"
            )

            if data is None or data.empty:
                return pd.DataFrame()

            if isinstance(data.index, pd.MultiIndex):
                data = data.droplevel(0)

            # 重命名列
            new_columns = {}
            for col in data.columns:
                if col.startswith("$"):
                    new_columns[col] = col[1:]
            data = data.rename(columns=new_columns)

            return ensure_datetime_index(data)

        except Exception as e:
            logger.error(f"获取财务数据失败: {code}, {e}")
            return pd.DataFrame()

    def get_trading_calendar(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        market: str = "cn"
    ) -> List[datetime]:
        """
        获取交易日历
        Get trading calendar

        使用 qlib 获取交易日历。
        Use qlib to get trading calendar.

        Args:
            start_date: 开始日期 / Start date
            end_date: 结束日期 / End date
            market: 市场代码 / Market code

        Returns:
            交易日列表 / Trading days list
        """
        self._ensure_initialized()

        try:
            from qlib.data import D

            start = parse_date(start_date)
            end = parse_date(end_date)

            # 使用 qlib 的交易日历
            trading_days = D.calendar(
                freq="day",
                start_time=start.strftime("%Y-%m-%d"),
                end_time=end.strftime("%Y-%m-%d")
            )

            if trading_days is None:
                return []

            # 转换为 datetime 列表
            return [pd.Timestamp(t).to_pydatetime() for t in trading_days]

        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            # 返回简单的工作日列表
            return self._get_simple_trading_days(start_date, end_date)

    def get_concepts(self, code: str) -> List[str]:
        """
        获取股票概念板块
        Get stock concept sectors

        Args:
            code: 股票代码 / Stock code

        Returns:
            概念板块列表 / Concept sector list
        """
        self._ensure_initialized()

        try:
            from qlib.data import D

            code = normalize_stock_code(code)
            qlib_code = code.split(".")[0]

            # qlib 概念数据需要扩展支持
            # 这里返回空列表，由其他数据源补充
            return []

        except Exception:
            return []

    def _get_exchange(self, code: str) -> str:
        """
        根据股票代码判断交易所
        Determine exchange based on stock code

        Args:
            code: 股票代码 / Stock code

        Returns:
            交易所名称 / Exchange name
        """
        code = code.replace(".", "").upper()

        if code.startswith("6"):
            return "SH"  # 上海证券交易所
        elif code.startswith(("0", "3")):
            return "SZ"  # 深圳证券交易所
        elif code.startswith(("4", "8")):
            return "BJ"  # 北京证券交易所
        else:
            return "SZ"  # 默认深圳

    def _get_simple_trading_days(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> List[datetime]:
        """
        获取简单的交易日列表（排除周末）
        Get simple trading days list (excluding weekends)

        Args:
            start_date: 开始日期 / Start date
            end_date: 结束日期 / End date

        Returns:
            交易日列表 / Trading days list
        """
        start = parse_date(start_date)
        end = parse_date(end_date)

        trading_days = []
        current = start
        while current <= end:
            if current.weekday() < 5:  # 周一到周五
                trading_days.append(current)
            current += timedelta(days=1)

        return trading_days


# ==================== 便捷函数 / Convenience Functions ====================

def create_qlib_provider(provider_uri: Optional[str] = None) -> QlibDataProvider:
    """
    创建 qlib 数据提供者的便捷函数
    Convenience function to create qlib data provider

    Args:
        provider_uri: qlib 数据路径 / qlib data path

    Returns:
        qlib 数据提供者实例 / qlib data provider instance
    """
    config = {}
    if provider_uri:
        config["provider_uri"] = provider_uri

    return QlibDataProvider(config)