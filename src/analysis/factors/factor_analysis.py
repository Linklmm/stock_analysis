"""
因子分析模块
Factor Analysis Module

该模块提供因子分析功能，包括因子计算、因子检验等。
This module provides factor analysis functionality, including factor calculation and testing.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np
from scipy import stats

from src.core.utils import logger
from config.settings import FACTORS


class FactorAnalyzer:
    """
    因子分析器
    Factor Analyzer

    分析因子的有效性和表现。
    Analyze factor effectiveness and performance.

    Attributes:
        factors: 因子列表
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化因子分析器

        Args:
            config: 配置
        """
        self.config = config or {}
        self.factors = FACTORS

    def calculate_factors(
        self,
        data: pd.DataFrame,
        factor_names: List[str] = None
    ) -> pd.DataFrame:
        """
        计算因子
        Calculate factors

        Args:
            data: 价格数据
            factor_names: 因子名称列表

        Returns:
            包含因子的 DataFrame
        """
        result = data.copy()

        if factor_names is None:
            factor_names = [
                "momentum", "volatility", "volume_ratio",
                "rsi_factor", "macd_factor"
            ]

        for factor_name in factor_names:
            try:
                if factor_name == "momentum":
                    result["momentum_5d"] = result["close"].pct_change(5)
                    result["momentum_20d"] = result["close"].pct_change(20)

                elif factor_name == "volatility":
                    returns = result["close"].pct_change()
                    result["volatility_20d"] = returns.rolling(20).std() * np.sqrt(252)

                elif factor_name == "volume_ratio":
                    result["volume_ratio"] = result["volume"] / result["volume"].rolling(20).mean()

                elif factor_name == "rsi_factor":
                    result["rsi_factor"] = self._calculate_rsi(result["close"], 14)

                elif factor_name == "macd_factor":
                    result["macd_factor"] = self._calculate_macd_signal(result["close"])

            except Exception as e:
                logger.warning(f"计算因子 {factor_name} 失败: {e}")

        return result

    def _calculate_rsi(self, price: pd.Series, period: int = 14) -> pd.Series:
        """计算 RSI 因子"""
        delta = price.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd_signal(self, price: pd.Series) -> pd.Series:
        """计算 MACD 信号因子"""
        ema12 = price.ewm(span=12, adjust=False).mean()
        ema26 = price.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()

        return (macd - signal) / price

    def analyze_factor_effectiveness(
        self,
        factor_data: pd.DataFrame,
        factor_col: str,
        return_col: str = "return_5d",
        n_groups: int = 5
    ) -> Dict[str, Any]:
        """
        分析因子有效性
        Analyze factor effectiveness

        Args:
            factor_data: 因子数据
            factor_col: 因子列名
            return_col: 收益率列名
            n_groups: 分组数

        Returns:
            分析结果
        """
        # 准备数据
        data = factor_data[[factor_col, return_col]].dropna()

        if len(data) < n_groups * 10:
            return {"error": "数据量不足"}

        # 分组
        data["group"] = pd.qcut(data[factor_col], n_groups, labels=False, duplicates="drop")

        # 计算各组收益率
        group_returns = data.groupby("group")[return_col].mean()

        # IC 分析
        ic = data[factor_col].corr(data[return_col])

        # Rank IC
        rank_ic = data[factor_col].rank().corr(data[return_col].rank())

        # 多空收益
        long_return = group_returns.iloc[-1] if len(group_returns) > 0 else 0
        short_return = group_returns.iloc[0] if len(group_returns) > 0 else 0
        long_short_return = long_return - short_return

        return {
            "factor": factor_col,
            "ic": float(ic),
            "rank_ic": float(rank_ic),
            "group_returns": group_returns.to_dict(),
            "long_return": float(long_return),
            "short_return": float(short_return),
            "long_short_return": float(long_short_return),
            "n_groups": len(group_returns)
        }

    def calculate_ic_series(
        self,
        factor_data: pd.DataFrame,
        factor_col: str,
        return_col: str = "return_5d"
    ) -> pd.Series:
        """
        计算IC时间序列
        Calculate IC time series

        Args:
            factor_data: 因子数据
            factor_col: 因子列名
            return_col: 收益率列名

        Returns:
            IC序列
        """
        # 按日期计算IC
        if isinstance(factor_data.index, pd.DatetimeIndex):
            ic_series = factor_data.groupby(factor_data.index.date).apply(
                lambda x: x[factor_col].corr(x[return_col])
            )
            return ic_series

        return pd.Series([factor_data[factor_col].corr(factor_data[return_col])])

    def factor_regression(
        self,
        factor_data: pd.DataFrame,
        factor_cols: List[str],
        return_col: str = "return_5d"
    ) -> Dict[str, Any]:
        """
        因子回归分析
        Factor regression analysis

        Args:
            factor_data: 因子数据
            factor_cols: 因子列名列表
            return_col: 收益率列名

        Returns:
            回归结果
        """
        try:
            import statsmodels.api as sm

            data = factor_data[factor_cols + [return_col]].dropna()

            X = sm.add_constant(data[factor_cols])
            y = data[return_col]

            model = sm.OLS(y, X).fit()

            return {
                "r_squared": float(model.rsquared),
                "adj_r_squared": float(model.rsquared_adj),
                "coefficients": model.params.to_dict(),
                "p_values": model.pvalues.to_dict(),
                "t_values": model.tvalues.to_dict()
            }

        except ImportError:
            logger.warning("statsmodels 未安装，跳过回归分析")
            return {"error": "statsmodels 未安装"}


def analyze_factors(
    data: pd.DataFrame,
    factor_names: List[str] = None
) -> pd.DataFrame:
    """
    分析因子的便捷函数
    Convenience function to analyze factors

    Args:
        data: 数据
        factor_names: 因子名称列表

    Returns:
        因子数据
    """
    analyzer = FactorAnalyzer()
    return analyzer.calculate_factors(data, factor_names)