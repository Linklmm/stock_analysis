"""
市场资讯数据获取模块
Market News Data Module

提供财经新闻、涨停股票池、股票公告等数据获取功能。
Uses AkShare API for data fetching with caching support.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from typing import Optional, List, Dict
import streamlit as st

from src.core.utils import logger


class MarketNewsProvider:
    """
    市场资讯数据提供者
    Provides market news data from AkShare API
    """

    def __init__(self):
        self._akshare_available = None

    def _check_akshare(self) -> bool:
        """检查 AkShare 是否可用"""
        if self._akshare_available is not None:
            return self._akshare_available

        try:
            import akshare as ak
            self._akshare_available = True
            return True
        except Exception:
            self._akshare_available = False
            return False

    @st.cache_data(ttl=300, show_spinner=False)  # 5分钟缓存
    def get_financial_news(_self, count: int = 20) -> List[Dict]:
        """
        获取财经新闻

        Args:
            count: 获取新闻数量

        Returns:
            新闻列表，每条包含 title, content, publish_time, source, url
        """
        if not _self._check_akshare():
            logger.warning("AkShare 不可用")
            return []

        try:
            import akshare as ak

            # 东方财富财经新闻
            df = ak.stock_news_em(symbol="财经")

            if df is None or df.empty:
                return []

            news_list = []
            for _, row in df.head(count).iterrows():
                news_list.append({
                    "title": row.get("新闻标题", ""),
                    "content": row.get("新闻内容", ""),
                    "publish_time": row.get("发布时间", ""),
                    "source": row.get("文章来源", ""),
                    "url": row.get("新闻链接", ""),
                })

            logger.info(f"获取财经新闻成功，共 {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.error(f"获取财经新闻失败: {e}")
            return []

    @st.cache_data(ttl=60, show_spinner=False)  # 1分钟缓存
    def get_limit_up_stocks(_self) -> Dict:
        """
        获取涨停股票池

        Returns:
            包含涨停统计和涨停股票列表
        """
        if not _self._check_akshare():
            logger.warning("AkShare 不可用")
            return {"total": 0, "continuous_count": 0, "stocks": []}

        try:
            import akshare as ak

            # 涨停股票池
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))

            if df is None or df.empty:
                return {"total": 0, "continuous_count": 0, "stocks": []}

            stocks = []
            continuous_count = 0

            for _, row in df.iterrows():
                # 统计连板股
                continuous = row.get("连板数", 1)
                if continuous and continuous >= 2:
                    continuous_count += 1

                stocks.append({
                    "code": row.get("代码", ""),
                    "name": row.get("名称", ""),
                    "pct_chg": row.get("涨跌幅", 0),
                    "continuous": continuous,
                    "seal_time": row.get("涨停统计", {}).get("首次涨停时间", "") if isinstance(row.get("涨停统计"), dict) else "",
                    "industry": row.get("所属行业", ""),
                    "seal_amount": row.get("封板资金", 0),
                    "reason": row.get("涨停原因类别", ""),
                })

            result = {
                "total": len(stocks),
                "continuous_count": continuous_count,
                "stocks": stocks,
            }

            logger.info(f"获取涨停股票池成功，共 {len(stocks)} 只")
            return result

        except Exception as e:
            logger.error(f"获取涨停股票池失败: {e}")
            return {"total": 0, "continuous_count": 0, "stocks": []}

    @st.cache_data(ttl=300, show_spinner=False)  # 5分钟缓存
    def get_stock_announcements(_self, count: int = 50, announcement_type: str = None) -> List[Dict]:
        """
        获取股票公告

        Args:
            count: 获取公告数量
            announcement_type: 公告类型筛选 (可选)

        Returns:
            公告列表
        """
        if not _self._check_akshare():
            logger.warning("AkShare 不可用")
            return []

        try:
            import akshare as ak

            # 获取公告数据
            df = ak.stock_notice_report()

            if df is None or df.empty:
                return []

            announcements = []

            for _, row in df.head(count).iterrows():
                ann = {
                    "code": row.get("代码", ""),
                    "name": row.get("名称", ""),
                    "title": row.get("公告标题", ""),
                    "type": row.get("公告类型", ""),
                    "date": row.get("公告日期", ""),
                    "url": row.get("公告链接", ""),
                }

                # 类型筛选
                if announcement_type and announcement_type != "全部":
                    if announcement_type not in ann.get("type", ""):
                        continue

                announcements.append(ann)

            logger.info(f"获取股票公告成功，共 {len(announcements)} 条")
            return announcements

        except Exception as e:
            logger.error(f"获取股票公告失败: {e}")
            return []


# 全局实例
_news_provider = MarketNewsProvider()


def get_financial_news(count: int = 20) -> List[Dict]:
    """获取财经新闻"""
    return _news_provider.get_financial_news(count)


def get_limit_up_stocks() -> Dict:
    """获取涨停股票池"""
    return _news_provider.get_limit_up_stocks()


def get_stock_announcements(count: int = 50, announcement_type: str = None) -> List[Dict]:
    """获取股票公告"""
    return _news_provider.get_stock_announcements(count, announcement_type)