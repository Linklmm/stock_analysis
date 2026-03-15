"""
实时行情获取模块
Real-time Market Data Module

支持多种数据源，优先使用 Tushare，AkShare 作为备用。
数据自动缓存到 MySQL 数据库。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta, date
from typing import Dict, Optional, List

import pandas as pd
import numpy as np

from src.core.utils import logger
from src.data.database import db_manager, StockDaily, IndexDaily


class MarketDataProvider:
    """
    市场数据提供者
    支持多种数据源
    """

    def __init__(self):
        self._akshare_available = None
        self._tushare_available = None
        self._tushare_pro = None

    def _check_akshare(self) -> bool:
        """检查 AkShare 是否可用"""
        if self._akshare_available is not None:
            return self._akshare_available

        try:
            import akshare as ak
            # 简单测试
            self._akshare_available = True
            return True
        except Exception:
            self._akshare_available = False
            return False

    def _check_tushare(self) -> bool:
        """检查 Tushare 是否可用"""
        if self._tushare_available is not None:
            return self._tushare_available

        try:
            import tushare as ts
            import os

            token = os.environ.get("TUSHARE_TOKEN")
            if token:
                ts.set_token(token)
                self._tushare_pro = ts.pro_api()
                self._tushare_available = True
                return True

            self._tushare_available = False
            return False
        except Exception:
            self._tushare_available = False
            return False

    def get_index_data(self) -> Dict[str, Dict]:
        """
        获取指数数据
        优先从 MySQL 缓存读取，否则从数据源获取
        """
        # 尝试从 MySQL 缓存获取今日数据
        cached_data = self._get_index_from_mysql()
        if cached_data:
            logger.info("从 MySQL 缓存获取指数数据成功")
            return cached_data

        # 优先尝试 AkShare（使用历史数据接口，更稳定）
        if self._check_akshare():
            try:
                data = self._get_index_from_akshare()
                if data:
                    return data
            except Exception as e:
                logger.warning(f"AkShare 获取指数失败: {e}")

        # 尝试 Tushare 作为备用
        if self._check_tushare():
            try:
                data = self._get_index_from_tushare()
                if data:
                    return data
            except Exception as e:
                logger.warning(f"Tushare 获取指数失败: {e}")

        # 使用默认数据
        logger.warning("所有数据源不可用，使用默认数据")
        return self._get_default_index_data()

    def _get_index_from_akshare(self) -> Dict[str, Dict]:
        """
        从 AkShare 获取指数数据并保存到 MySQL
        使用 stock_zh_index_daily 接口获取历史数据，取最新一条
        """
        import akshare as ak

        result = {}
        df_list = []

        # 指数代码映射 (AkShare stock_zh_index_daily 格式 -> TS格式)
        index_codes = {
            "上证指数": ("sh000001", "000001.SH"),
            "深证成指": ("sz399001", "399001.SZ"),
            "创业板指": ("sz399006", "399006.SZ"),
            "科创50": ("sh000688", "000688.SH"),
        }

        for name, (ak_code, ts_code) in index_codes.items():
            try:
                # 使用历史数据接口获取最近数据
                df = ak.stock_zh_index_daily(symbol=ak_code)

                if df is not None and not df.empty:
                    # 获取最近几天的数据保存到数据库
                    recent_df = df.tail(10).copy()
                    recent_df = recent_df.rename(columns={"date": "trade_date"})

                    for _, row in recent_df.iterrows():
                        df_list.append({
                            "ts_code": ts_code,
                            "trade_date": row["trade_date"],
                            "open": row.get("open"),
                            "high": row.get("high"),
                            "low": row.get("low"),
                            "close": row.get("close"),
                            "pre_close": None,
                            "change": None,
                            "pct_chg": None,
                            "vol": row.get("volume"),
                            "amount": None
                        })

                    # 获取最新一条数据
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest

                    close = float(latest["close"])
                    pre_close = float(prev["close"])
                    change_pct = round((close - pre_close) / pre_close * 100, 2) if pre_close > 0 else 0

                    result[name] = {
                        "value": close,
                        "change_pct": change_pct,
                    }

                    logger.debug(f"AkShare 获取 {name} 成功: {close}, {change_pct}%")
            except Exception as e:
                logger.warning(f"AkShare 获取 {name} 失败: {e}")

        # 保存到 MySQL
        if df_list:
            try:
                save_df = pd.DataFrame(df_list)
                # 计算涨跌幅和昨收价
                save_df = save_df.sort_values(["ts_code", "trade_date"])
                for ts_code in save_df["ts_code"].unique():
                    mask = save_df["ts_code"] == ts_code
                    save_df.loc[mask, "pre_close"] = save_df.loc[mask, "close"].shift(1)
                    pre_close = save_df.loc[mask, "pre_close"]
                    close = save_df.loc[mask, "close"]
                    save_df.loc[mask, "pct_chg"] = round(
                        (close - pre_close) / pre_close * 100, 2
                    ).where(pre_close.notna() & (pre_close != 0), 0)

                # 将 NaN 替换为 None（MySQL 不支持 NaN）
                save_df = save_df.where(pd.notna(save_df), None)
                db_manager.save_index_daily(save_df)
            except Exception as e:
                logger.warning(f"保存指数数据到 MySQL 失败: {e}")

        if result:
            logger.info(f"AkShare 获取指数成功，共 {len(result)} 个指数")
            return result

        raise Exception("AkShare 返回数据为空")

    def _get_index_from_mysql(self) -> Optional[Dict[str, Dict]]:
        """从 MySQL 缓存获取指数数据"""
        result = {}

        index_codes = {
            "上证指数": "000001.SH",
            "深证成指": "399001.SZ",
            "创业板指": "399006.SZ",
            "科创50": "000688.SH",
        }

        for name, code in index_codes.items():
            data = db_manager.get_latest_index_data(code)
            if data:
                # 检查数据是否为今天
                if data["trade_date"] == date.today():
                    result[name] = {
                        "value": data["close"],
                        "change_pct": data["pct_chg"],
                    }

        return result if len(result) == len(index_codes) else None

    def _get_index_from_tushare(self) -> Dict[str, Dict]:
        """从 Tushare 获取指数并保存到 MySQL"""
        result = {}
        df_list = []

        index_codes = {
            "上证指数": "000001.SH",
            "深证成指": "399001.SZ",
            "创业板指": "399006.SZ",
            "科创50": "000688.SH",
        }

        today = datetime.now().strftime("%Y%m%d")

        for name, code in index_codes.items():
            try:
                df = self._tushare_pro.index_daily(
                    ts_code=code,
                    start_date=today,
                    end_date=today
                )

                if not df.empty:
                    row = df.iloc[0]
                    pre_close = float(row.get("pre_close", 1))
                    close = float(row.get("close", 0))
                    change_pct = float(row.get("pct_chg", 0))

                    result[name] = {
                        "value": close,
                        "change_pct": change_pct,
                    }

                    # 准备保存到 MySQL 的数据
                    df_list.append({
                        "ts_code": code,
                        "trade_date": today,
                        "open": row.get("open"),
                        "high": row.get("high"),
                        "low": row.get("low"),
                        "close": close,
                        "pre_close": pre_close,
                        "change": row.get("change"),
                        "pct_chg": change_pct,
                        "vol": row.get("vol"),
                        "amount": row.get("amount")
                    })
            except Exception as e:
                logger.debug(f"Tushare 获取 {name} 失败: {e}")

        if result:
            # 保存到 MySQL
            if df_list:
                try:
                    db_manager.save_index_daily(pd.DataFrame(df_list))
                except Exception as e:
                    logger.warning(f"保存指数数据到 MySQL 失败: {e}")

            logger.info("Tushare 获取指数成功")
            return result

        raise Exception("Tushare 返回数据为空")

    def _get_default_index_data(self) -> Dict[str, Dict]:
        """默认指数数据（当所有数据源不可用时）"""
        return {
            "上证指数": {"value": 0, "change_pct": 0},
            "深证成指": {"value": 0, "change_pct": 0},
            "创业板指": {"value": 0, "change_pct": 0},
            "科创50": {"value": 0, "change_pct": 0},
        }

    def get_stock_history(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据

        优先级：
        1. MySQL 缓存（完全匹配则直接返回）
        2. 如果部分匹配，补充获取缺失日期
        3. AkShare API（主要数据源）
        4. Tushare API（备用，需要权限）

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        # 提取纯数字代码
        code_num = code.split(".")[0]

        # 转换为 TS 代码格式
        if code.startswith("6"):
            ts_code = f"{code_num}.SH"
        else:
            ts_code = f"{code_num}.SZ"

        # 先尝试从 MySQL 缓存获取
        cached_df = self._get_history_from_mysql(ts_code, start_date, end_date)
        if cached_df is not None and not cached_df.empty:
            # 检查数据完整性（简单判断：数据量是否合理）
            expected_days = self._estimate_trading_days(start_date, end_date)
            if len(cached_df) >= expected_days * 0.8:  # 80%以上数据存在即认为完整
                logger.info(f"从 MySQL 缓存获取历史数据: {len(cached_df)} 条")
                return cached_df
            else:
                logger.info(f"MySQL 缓存数据不完整({len(cached_df)}/{expected_days})，从 API 补充")

        # 从 API 获取数据
        df = None

        # 优先尝试 AkShare（主要数据源）
        if self._check_akshare():
            try:
                df = self._get_history_from_akshare(ts_code, code_num, start_date, end_date)
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"AkShare 获取历史数据失败: {e}")

        # 尝试 Tushare 作为备用
        if self._check_tushare():
            try:
                df = self._get_history_from_tushare(ts_code, start_date, end_date)
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Tushare 获取历史数据失败: {e}")

        # 如果 API 都失败了，返回缓存数据（即使不完整）
        if cached_df is not None and not cached_df.empty:
            logger.warning(f"API 获取失败，返回不完整的缓存数据: {len(cached_df)} 条")
            return cached_df

        logger.error("所有数据源不可用")
        return None

    def _estimate_trading_days(self, start_date: str, end_date: str) -> int:
        """
        估算交易日数量
        Estimate number of trading days
        """
        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # 大约每年 250 个交易日，每月约 21 个交易日
        days = (end - start).days
        # 排除周末
        trading_days = days * 5 // 7
        # 考虑节假日（粗略估计）
        return int(trading_days * 0.9)

    def _get_history_from_mysql(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 MySQL 缓存获取历史数据"""
        try:
            return db_manager.get_stock_daily(ts_code, start_date, end_date)
        except Exception as e:
            logger.debug(f"MySQL 缓存获取失败: {e}")
            return None

    def _get_history_from_akshare(
        self,
        ts_code: str,
        code: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        从 AkShare 获取历史数据并保存到 MySQL

        Args:
            ts_code: TS代码格式 (如 000001.SZ)
            code: 纯数字代码 (如 000001)
            start_date: 开始日期
            end_date: 结束日期
        """
        import akshare as ak

        start = start_date.replace("-", "")
        end = end_date.replace("-", "")

        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq"
        )

        if df.empty:
            return None

        # 重命名列
        column_mapping = {
            "日期": "trade_date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "换手率": "turnover"
        }
        df = df.rename(columns=column_mapping)

        # 添加必要字段
        df["ts_code"] = ts_code
        df["trade_date"] = pd.to_datetime(df["trade_date"])

        # 计算昨收价
        df["pre_close"] = df["close"].shift(1)
        df.loc[df.index[0], "pre_close"] = df["close"].iloc[0] / (1 + df["pct_chg"].iloc[0] / 100) if df["pct_chg"].iloc[0] != 0 else df["close"].iloc[0]

        # 保存到 MySQL
        try:
            save_df = df[["ts_code", "trade_date", "open", "high", "low", "close",
                         "pre_close", "change", "pct_chg", "volume", "amount"]].copy()
            # 将 NaN 替换为 None（MySQL 不支持 NaN）
            save_df = save_df.where(pd.notna(save_df), None)
            db_manager.save_stock_daily(save_df)
            logger.info(f"历史数据已保存到 MySQL: {len(save_df)} 条")
        except Exception as e:
            logger.warning(f"保存历史数据到 MySQL 失败: {e}")

        # 格式化返回数据
        df = df.set_index("trade_date").sort_index()
        df["code"] = code

        logger.info(f"AkShare 获取历史数据成功: {len(df)} 条")
        return df[["open", "high", "low", "close", "volume", "amount", "code"]]

    def _get_history_from_tushare(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 Tushare 获取历史数据并保存到 MySQL"""
        start = start_date.replace("-", "")
        end = end_date.replace("-", "")

        df = self._tushare_pro.daily(
            ts_code=ts_code,
            start_date=start,
            end_date=end
        )

        if df.empty:
            return None

        # 重命名和格式化
        df = df.rename(columns={
            "trade_date": "datetime",
            "vol": "volume",
        })
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()

        # 选择需要的列
        df = df[["open", "high", "low", "close", "volume", "amount", "ts_code", "pre_close", "change", "pct_chg"]]

        # 保存到 MySQL
        try:
            save_df = df.reset_index()
            save_df = save_df.rename(columns={"datetime": "trade_date"})
            db_manager.save_stock_daily(save_df)
        except Exception as e:
            logger.warning(f"保存股票历史数据到 MySQL 失败: {e}")

        # 添加代码列用于返回
        code_num = ts_code.split(".")[0]
        df["code"] = code_num

        logger.info(f"Tushare 获取历史数据成功: {len(df)} 条")
        return df[["open", "high", "low", "close", "volume", "amount", "code"]]

    def get_realtime_stock(self, code: str) -> Optional[Dict]:
        """获取实时股票数据"""
        code_num = code.split(".")[0]

        # 转换为 TS 代码格式
        if code.startswith("6"):
            ts_code = f"{code_num}.SH"
        else:
            ts_code = f"{code_num}.SZ"

        # 方法1: 尝试 AkShare 实时接口
        if self._check_akshare():
            try:
                import akshare as ak
                df = ak.stock_zh_a_spot_em()
                row = df[df["代码"] == code_num]

                if not row.empty:
                    data = row.iloc[0]
                    return {
                        "code": code,
                        "name": data.get("名称", code),
                        "price": float(data.get("最新价", 0)),
                        "open": float(data.get("今开", 0)),
                        "high": float(data.get("最高", 0)),
                        "low": float(data.get("最低", 0)),
                        "volume": float(data.get("成交量", 0)),
                        "amount": float(data.get("成交额", 0)),
                        "change_pct": float(data.get("涨跌幅", 0)),
                        "turnover": float(data.get("换手率", 0)),
                    }
            except Exception as e:
                logger.debug(f"AkShare 实时接口失败: {e}")

        # 方法2: 通过历史数据获取最新数据
        if self._check_akshare():
            try:
                import akshare as ak
                from datetime import datetime, timedelta

                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

                df = ak.stock_zh_a_hist(
                    symbol=code_num,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )

                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    close = float(latest.get("收盘", 0))
                    pre_close = float(prev.get("收盘", 0))
                    change_pct = round((close - pre_close) / pre_close * 100, 2) if pre_close > 0 else 0

                    return {
                        "code": code,
                        "name": code,
                        "price": close,
                        "open": float(latest.get("开盘", 0)),
                        "high": float(latest.get("最高", 0)),
                        "low": float(latest.get("最低", 0)),
                        "volume": float(latest.get("成交量", 0)),
                        "amount": float(latest.get("成交额", 0)),
                        "change_pct": change_pct,
                        "turnover": 0,
                    }
            except Exception as e:
                logger.debug(f"AkShare 历史数据获取最新数据失败: {e}")

        # 方法3: 从 MySQL 缓存获取最近的数据
        try:
            df = db_manager.get_stock_daily(ts_code)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                return {
                    "code": code,
                    "name": code,
                    "price": float(latest.get("close", 0)),
                    "open": float(latest.get("open", 0)),
                    "high": float(latest.get("high", 0)),
                    "low": float(latest.get("low", 0)),
                    "volume": float(latest.get("vol", 0)),
                    "amount": float(latest.get("amount", 0)),
                    "change_pct": float(latest.get("pct_chg", 0)),
                    "turnover": 0,
                }
        except Exception as e:
            logger.debug(f"MySQL 缓存获取实时数据失败: {e}")

        return None


# 全局实例
_provider = MarketDataProvider()


def get_realtime_index_data() -> Dict[str, Dict]:
    """获取实时指数数据"""
    return _provider.get_index_data()


def get_stock_history(code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """获取股票历史数据"""
    return _provider.get_stock_history(code, start_date, end_date)


def get_realtime_stock_data(code: str) -> Optional[Dict]:
    """获取实时股票数据"""
    return _provider.get_realtime_stock(code)