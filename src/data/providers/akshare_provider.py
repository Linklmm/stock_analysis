"""AkShare 数据提供者"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from src.data.base import DataProvider, DataFrequency, StockInfo
from src.core.exceptions import DataSourceError
from src.core.utils import logger, parse_date, normalize_stock_code


class AkShareDataProvider(DataProvider):
    """AkShare 数据提供者"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("akshare", config)

    def initialize(self) -> bool:
        try:
            import akshare as ak
            self._ak = ak
            self._initialized = True
            logger.info("AkShare 初始化成功")
            return True

        except ImportError:
            logger.error("AkShare 未安装")
            return False

    def is_available(self) -> bool:
        return self._initialized

    def get_stock_list(self, market: str = "cn") -> pd.DataFrame:
        self._ensure_initialized()
        try:
            df = self._ak.stock_zh_a_spot_em()
            return df
        except Exception as e:
            raise DataSourceError("akshare", "获取股票列表失败", str(e))

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        self._ensure_initialized()
        try:
            code_num = code.split(".")[0]
            df = self._ak.stock_individual_info_em(symbol=code_num)

            if df.empty:
                return None

            info = dict(zip(df["item"], df["value"]))

            return StockInfo(
                code=code,
                name=info.get("股票简称", code),
                exchange=self._get_exchange(code),
                industry=info.get("行业")
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
            code_num = code.split(".")[0]

            start = parse_date(start_date).strftime("%Y%m%d")
            end = parse_date(end_date).strftime("%Y%m%d")

            df = self._ak.stock_zh_a_hist(
                symbol=code_num,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq"
            )

            if df.empty:
                return pd.DataFrame()

            # 重命名列
            column_mapping = {
                "日期": "datetime",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "pct_change",
                "涨跌额": "change",
                "换手率": "turnover"
            }
            df = df.rename(columns=column_mapping)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()

            return df

        except Exception as e:
            raise DataSourceError("akshare", f"获取行情数据失败: {code}", str(e))

    def get_index_data(
        self,
        index_code: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        frequency: DataFrequency = DataFrequency.DAY
    ) -> pd.DataFrame:
        self._ensure_initialized()
        try:
            # AkShare 指数代码
            index_map = {
                "000001.SH": "sh000001",
                "399001.SZ": "sz399001",
                "000300.SH": "sh000300"
            }

            ak_code = index_map.get(index_code, index_code.lower().replace(".sh", "").replace(".sz", ""))

            start = parse_date(start_date).strftime("%Y%m%d")
            end = parse_date(end_date).strftime("%Y%m%d")

            df = self._ak.stock_zh_index_daily(symbol=ak_code)

            if df.empty:
                return pd.DataFrame()

            df = df.rename(columns={"date": "datetime"})
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()

            # 筛选日期范围
            df = df[(df.index >= start) & (df.index <= end)]

            return df

        except Exception as e:
            raise DataSourceError("akshare", f"获取指数数据失败: {index_code}", str(e))

    def get_financial_data(
        self,
        code: str,
        report_type: str = "all",
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        self._ensure_initialized()
        try:
            code_num = code.split(".")[0]

            df = self._ak.stock_financial_analysis_indicator(symbol=code_num)
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
            df = self._ak.tool_trade_date_hist_sina()

            dates = pd.to_datetime(df["trade_date"]).tolist()

            start = parse_date(start_date)
            end = parse_date(end_date)

            return [d for d in dates if start <= d <= end]

        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return []

    def _get_exchange(self, code: str) -> str:
        code = code.replace(".", "").upper()
        if code.startswith("6"):
            return "SH"
        elif code.startswith(("0", "3")):
            return "SZ"
        elif code.startswith(("4", "8")):
            return "BJ"
        return "SZ"