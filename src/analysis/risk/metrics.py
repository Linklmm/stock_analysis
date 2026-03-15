"""风险指标计算模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, Optional

import pandas as pd
import numpy as np
from scipy import stats

from src.core.utils import logger


def calculate_risk_metrics(
    data: pd.DataFrame,
    risk_free_rate: float = 0.03
) -> Dict[str, float]:
    """
    计算风险指标
    Calculate risk metrics

    Args:
        data: 价格数据
        risk_free_rate: 无风险利率

    Returns:
        风险指标字典
    """
    if "close" not in data.columns:
        return {}

    returns = data["close"].pct_change().dropna()

    if len(returns) < 20:
        return {}

    # 波动率（年化）
    volatility = returns.std() * np.sqrt(252)

    # 下行波动率
    negative_returns = returns[returns < 0]
    downside_volatility = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0

    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min())

    # 夏普比率
    excess_return = returns.mean() * 252 - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0

    # 索提诺比率
    sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0

    # VaR (95%)
    var_95 = np.percentile(returns, 5)

    # CVaR (条件VaR)
    cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95

    # 偏度和峰度
    skewness = stats.skew(returns)
    kurtosis = stats.kurtosis(returns)

    return {
        "volatility": float(volatility),
        "downside_volatility": float(downside_volatility),
        "max_drawdown": float(max_drawdown),
        "sharpe_ratio": float(sharpe_ratio),
        "sortino_ratio": float(sortino_ratio),
        "var_95": float(var_95),
        "cvar_95": float(cvar_95),
        "skewness": float(skewness),
        "kurtosis": float(kurtosis),
        "total_return": float((data["close"].iloc[-1] / data["close"].iloc[0] - 1))
    }


def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    计算风险价值
    Calculate Value at Risk

    Args:
        returns: 收益率序列
        confidence: 置信水平

    Returns:
        VaR
    """
    return float(np.percentile(returns, (1 - confidence) * 100))


def calculate_cvar(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    计算条件风险价值
    Calculate Conditional Value at Risk

    Args:
        returns: 收益率序列
        confidence: 置信水平

    Returns:
        CVaR
    """
    var = calculate_var(returns, confidence)
    return float(returns[returns <= var].mean())