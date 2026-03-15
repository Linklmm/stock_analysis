"""
涨跌概率计算模块
Probability Calculation Module

该模块提供股票涨跌概率的计算功能，
使用多种方法综合评估涨跌可能性。

This module provides stock price movement probability calculation,
using multiple methods to comprehensively evaluate the probability.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats

from src.core.utils import logger


class ProbabilityCalculator:
    """
    涨跌概率计算器
    Probability Calculator

    使用统计方法和机器学习计算涨跌概率。
    Calculate probability using statistical methods and machine learning.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化概率计算器

        Args:
            config: 配置
        """
        self.config = config or {}

    def calculate_probability(
        self,
        data: pd.DataFrame,
        methods: List[str] = None,
        weights: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        计算综合涨跌概率
        Calculate comprehensive probability

        Args:
            data: 数据
            methods: 计算方法列表
            weights: 方法权重

        Returns:
            概率字典
        """
        if methods is None:
            methods = ["historical", "technical", "volatility"]

        if weights is None:
            weights = {method: 1.0 / len(methods) for method in methods}

        probabilities = {}

        # 历史统计概率
        if "historical" in methods:
            probabilities["historical"] = self._historical_probability(data)
            weights["historical"] = weights.get("historical", 0.3)

        # 技术指标概率
        if "technical" in methods:
            probabilities["technical"] = self._technical_probability(data)
            weights["technical"] = weights.get("technical", 0.4)

        # 波动率分析概率
        if "volatility" in methods:
            probabilities["volatility"] = self._volatility_probability(data)
            weights["volatility"] = weights.get("volatility", 0.3)

        # 计算加权平均
        total_weight = sum(weights.values())
        weighted_prob = sum(
            probabilities.get(method, 0.5) * weights.get(method, 0)
            for method in methods
        ) / total_weight

        return {
            "buy_probability": weighted_prob,
            "sell_probability": 1 - weighted_prob,
            "confidence": self._calculate_confidence(probabilities),
            "details": probabilities
        }

    def _historical_probability(self, data: pd.DataFrame) -> float:
        """
        基于历史统计的概率
        Historical statistics based probability

        使用历史收益率分布计算概率。
        """
        if "close" not in data.columns:
            return 0.5

        returns = data["close"].pct_change().dropna()

        if len(returns) < 20:
            return 0.5

        # 计算上涨天数比例
        up_days = (returns > 0).sum()
        total_days = len(returns)
        base_prob = up_days / total_days

        # 考虑近期趋势
        recent_returns = returns.tail(20)
        recent_up = (recent_returns > 0).sum() / len(recent_returns)

        # 加权组合
        prob = 0.6 * base_prob + 0.4 * recent_up

        return float(prob)

    def _technical_probability(self, data: pd.DataFrame) -> float:
        """
        基于技术指标的概率
        Technical indicator based probability
        """
        from src.analysis.technical import calculate_rsi, calculate_macd

        score = 0
        signals = 0

        try:
            # RSI 概率
            rsi_data = calculate_rsi(data)
            if not rsi_data.empty:
                rsi = rsi_data["rsi"].iloc[-1]
                if rsi < 30:
                    score += 0.7  # 超卖，上涨概率高
                elif rsi > 70:
                    score += 0.3  # 超买，下跌概率高
                else:
                    score += 0.5 + (50 - rsi) / 100  # 线性映射
                signals += 1

            # MACD 概率
            macd_data = calculate_macd(data)
            if not macd_data.empty:
                macd = macd_data["macd"].iloc[-1]
                signal = macd_data["signal"].iloc[-1]
                if macd > signal:
                    score += 0.6
                else:
                    score += 0.4
                signals += 1

        except Exception as e:
            logger.warning(f"技术指标计算失败: {e}")

        if signals > 0:
            return float(score / signals)
        return 0.5

    def _volatility_probability(self, data: pd.DataFrame) -> float:
        """
        基于波动率的概率
        Volatility based probability

        使用波动率分析计算概率。
        """
        if "close" not in data.columns:
            return 0.5

        returns = data["close"].pct_change().dropna()

        if len(returns) < 20:
            return 0.5

        # 计算波动率
        volatility = returns.std() * np.sqrt(252)

        # 计算偏度
        skewness = stats.skew(returns)

        # 偏度为正表示上涨概率高
        prob = 0.5 + skewness * 0.1

        # 考虑波动率水平
        if volatility > 0.4:  # 高波动
            prob = prob * 0.8 + 0.1  # 增加不确定性

        return float(np.clip(prob, 0.2, 0.8))

    def _calculate_confidence(self, probabilities: Dict[str, float]) -> float:
        """
        计算置信度
        Calculate confidence

        基于各方法概率的一致性计算置信度。
        """
        values = list(probabilities.values())
        if not values:
            return 0.0

        # 计算标准差作为一致性的度量
        std = np.std(values)

        # 标准差越小，置信度越高
        # 标准差为 0 时置信度为 1，标准差为 0.5 时置信度为 0
        confidence = max(0, 1 - std * 2)

        return float(confidence)

    def calculate_expected_return(
        self,
        data: pd.DataFrame,
        probability: float,
        horizon: int = 5
    ) -> Dict[str, float]:
        """
        计算预期收益
        Calculate expected return

        Args:
            data: 数据
            probability: 上涨概率
            horizon: 预测周期

        Returns:
            预期收益字典
        """
        returns = data["close"].pct_change().dropna()

        if len(returns) < horizon:
            return {
                "expected_return": 0,
                "upside": 0,
                "downside": 0
            }

        # 历史上涨跌幅
        up_returns = returns[returns > 0]
        down_returns = returns[returns < 0]

        avg_up = up_returns.mean() if len(up_returns) > 0 else 0
        avg_down = down_returns.mean() if len(down_returns) > 0 else 0

        # 预期收益
        expected_return = probability * avg_up + (1 - probability) * avg_down

        # 年化
        expected_return_annual = expected_return * (252 / horizon)

        return {
            "expected_return": float(expected_return),
            "expected_return_annual": float(expected_return_annual),
            "upside": float(avg_up),
            "downside": float(avg_down)
        }

    def monte_carlo_simulation(
        self,
        data: pd.DataFrame,
        days: int = 20,
        simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        蒙特卡洛模拟
        Monte Carlo simulation

        使用历史参数进行价格模拟。

        Args:
            data: 数据
            days: 模拟天数
            simulations: 模拟次数

        Returns:
            模拟结果
        """
        returns = data["close"].pct_change().dropna()

        if len(returns) < 30:
            return {
                "mean_return": 0,
                "probability_up": 0.5,
                "var_5": 0
            }

        # 估计参数
        mu = returns.mean()
        sigma = returns.std()

        # 模拟
        np.random.seed(42)
        simulated_returns = np.random.normal(mu, sigma, (simulations, days))

        # 计算累计收益
        cumulative_returns = np.prod(1 + simulated_returns, axis=1) - 1

        # 统计结果
        mean_return = np.mean(cumulative_returns)
        prob_up = np.mean(cumulative_returns > 0)
        var_5 = np.percentile(cumulative_returns, 5)

        return {
            "mean_return": float(mean_return),
            "probability_up": float(prob_up),
            "var_5": float(var_5),
            "percentile_25": float(np.percentile(cumulative_returns, 25)),
            "percentile_75": float(np.percentile(cumulative_returns, 75))
        }


def calculate_buy_probability(
    data: pd.DataFrame,
    methods: List[str] = None
) -> float:
    """
    计算买入概率的便捷函数
    Convenience function to calculate buy probability

    Args:
        data: 数据
        methods: 计算方法

    Returns:
        买入概率
    """
    calculator = ProbabilityCalculator()
    result = calculator.calculate_probability(data, methods)
    return result["buy_probability"]