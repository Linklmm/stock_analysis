"""
预测模块
Prediction Module

该模块提供趋势预测和概率计算功能。
This module provides trend prediction and probability calculation.
"""

from .trend_predictor import (
    TrendPredictor,
    predict_trend
)

from .probability import (
    ProbabilityCalculator,
    calculate_buy_probability
)

__all__ = [
    "TrendPredictor",
    "predict_trend",
    "ProbabilityCalculator",
    "calculate_buy_probability",
]