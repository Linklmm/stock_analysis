"""投资组合分析模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from src.core.utils import logger


class PortfolioAnalyzer:
    """投资组合分析器"""

    def __init__(self):
        pass

    def calculate_portfolio_return(
        self,
        weights: Dict[str, float],
        returns: pd.DataFrame
    ) -> pd.Series:
        """
        计算组合收益率
        Calculate portfolio return

        Args:
            weights: 权重字典
            returns: 各资产收益率 DataFrame

        Returns:
            组合收益率序列
        """
        # 将权重转换为 Series
        weight_series = pd.Series(weights)

        # 确保列匹配
        common_assets = list(set(weights.keys()) & set(returns.columns))
        weight_series = weight_series[common_assets]
        weight_series = weight_series / weight_series.sum()  # 归一化

        # 计算组合收益
        portfolio_return = (returns[common_assets] * weight_series).sum(axis=1)

        return portfolio_return

    def calculate_portfolio_volatility(
        self,
        weights: Dict[str, float],
        returns: pd.DataFrame
    ) -> float:
        """
        计算组合波动率
        Calculate portfolio volatility

        Args:
            weights: 权重字典
            returns: 各资产收益率 DataFrame

        Returns:
            组合波动率（年化）
        """
        weight_series = pd.Series(weights)
        common_assets = list(set(weights.keys()) & set(returns.columns))
        weight_series = weight_series[common_assets]
        weight_series = weight_series / weight_series.sum()

        # 协方差矩阵
        cov_matrix = returns[common_assets].cov()

        # 组合方差
        portfolio_variance = np.dot(weight_series, np.dot(cov_matrix, weight_series))

        # 年化波动率
        return float(np.sqrt(portfolio_variance * 252))


def analyze_portfolio(
    positions: Dict[str, float],
    returns: pd.DataFrame
) -> Dict[str, float]:
    """
    分析投资组合
    Analyze portfolio

    Args:
        positions: 持仓字典
        returns: 收益率 DataFrame

    Returns:
        分析结果
    """
    analyzer = PortfolioAnalyzer()

    portfolio_return = analyzer.calculate_portfolio_return(positions, returns)
    portfolio_volatility = analyzer.calculate_portfolio_volatility(positions, returns)

    # 计算累计收益
    cumulative_return = (1 + portfolio_return).cumprod().iloc[-1] - 1

    return {
        "total_return": float(cumulative_return),
        "volatility": float(portfolio_volatility),
        "sharpe_ratio": float((cumulative_return - 0.03) / portfolio_volatility) if portfolio_volatility > 0 else 0
    }