"""Tushare 数据提供者"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from src.data.base import DataProvider, DataFrequency, StockInfo
from src.core.exceptions import DataSourceError
from src.core.utils import logger, parse_date, normalize_stock_code
from config.settings import get_data_source_config


class TushareDataProvider(DataProvider):
    """Tushare 数据提供者"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("tushare", config)

        ds_config = get_data_source_config("tushare")
        self.api_key = self.config.get("api_key") or (ds_config.api_key if ds_config else None)
        self._pro = None

    def initialize(self) -> bool:
        try:
            import tushare as ts

            if not self.api_key:
                logger.error("Tushare token 未设置")
                return False

            ts.set_token(self.api_key)
            self._pro = ts.pro_api()
            self._initialized = True
            logger.info("Tushare 初始化成功")
            return True

        except ImportError:
            logger.error("Tushare 未安装")
            return False
        except Exception as e:
            logger.error(f"Tushare 初始化失败: {e}")
            return False

    def is_available(self) -> bool:
        return self._initialized and self._pro is not None

    def get_stock_list(self, market: str = "cn") -> pd.DataFrame:
        self._ensure_initialized()
        try:
            df = self._pro.stock_basic(exchange='', list_status='L')
            return df
        except Exception as e:
            raise DataSourceError("tushare", "获取股票列表失败", str(e))

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        self._ensure_initialized()
        try:
            ts_code = normalize_stock_code(code).replace(".SH", ".SH").replace(".SZ", ".SZ")
            df = self._pro.stock_basic(ts_code=ts_code)
            if df.empty:
                return None
            row = df.iloc[0]
            return StockInfo(
                code=code,
                name=row.get("name", code),
                exchange=row.get("exchange", ""),
                industry=row.get("industry")
            )
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None

    def get_market_data(
        self,
        code: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        frequency: DataFrequency = DataFrequency.DAY,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        self._ensure_initialized()
        try:
            ts_code = normalize_stock_code(code)
            ts_code = ts_code.replace(".SH", ".SH").replace(".SZ", ".SZ")

            start = parse_date(start_date).strftime("%Y%m%d")
            end = parse_date(end_date).strftime("%Y%m%d")

            df = self._pro.daily(ts_code=ts_code, start_date=start, end_date=end)

            if df.empty:
                return pd.DataFrame()

            df = df.rename(columns={"trade_date": "datetime", "vol": "volume"})
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()

            return df

        except Exception as e:
            raise DataSourceError("tushare", f"获取行情数据失败: {code}", str(e))

    def get_index_data(
        self,
        index_code: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        frequency: DataFrequency = DataFrequency.DAY
    ) -> pd.DataFrame:
        self._ensure_initialized()
        try:
            start = parse_date(start_date).strftime("%Y%m%d")
            end = parse_date(end_date).strftime("%Y%m%d")

            df = self._pro.index_daily(ts_code=index_code, start_date=start, end_date=end)

            if df.empty:
                return pd.DataFrame()

            df = df.rename(columns={"trade_date": "datetime", "vol": "volume"})
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()

            return df

        except Exception as e:
            raise DataSourceError("tushare", f"获取指数数据失败: {index_code}", str(e))

    def get_financial_data(
        self,
        code: str,
        report_type: str = "all",
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        self._ensure_initialized()
        try:
            ts_code = normalize_stock_code(code).replace(".SH", ".SH").replace(".SZ", ".SZ")

            df = self._pro.income(ts_code=ts_code)
            return df

        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return pd.DataFrame()

    def get_trading_calendar(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        market: str = "cn"
    ) -> List[datetime]:
        self._ensure_initialized()
        try:
            start = parse_date(start_date).strftime("%Y%m%d")
            end = parse_date(end_date).strftime("%Y%m%d")

            df = self._pro.trade_cal(exchange="SSE", start_date=start, end_date=end, is_open="1")

            dates = pd.to_datetime(df["cal_date"]).tolist()
            return dates

        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return []