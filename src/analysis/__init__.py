"""
分析模块
Analysis Module

该模块提供各种分析功能，包括：
- 分析引擎
- 趋势预测
- 技术分析
- 因子分析
- 回测
- 风险分析

This module provides various analysis functionality, including:
- Analysis engine
- Trend prediction
- Technical analysis
- Factor analysis
- Backtesting
- Risk analysis
"""

from .engine import (
    AnalysisEngine,
    AnalysisResult,
    create_engine
)

__all__ = [
    "AnalysisEngine",
    "AnalysisResult",
    "create_engine",
]