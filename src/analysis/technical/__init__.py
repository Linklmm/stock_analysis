"""
技术分析模块
Technical Analysis Module

该模块提供技术分析功能，包括：
- 技术指标计算
- 交易信号生成

This module provides technical analysis functionality, including:
- Technical indicator calculation
- Trading signal generation
"""

from .indicators import (
    # Moving Averages
    calculate_sma,
    calculate_ema,
    calculate_wma,
    calculate_all_ma,

    # Trend Indicators
    calculate_macd,
    calculate_bollinger,
    calculate_adx,

    # Momentum Indicators
    calculate_rsi,
    calculate_kdj,
    calculate_stochastic,
    calculate_cci,

    # Volatility Indicators
    calculate_atr,
    calculate_volatility,

    # Volume Indicators
    calculate_obv,
    calculate_vwap,
    calculate_mfi,

    # Comprehensive
    calculate_all_indicators,

    # Helpers
    detect_golden_cross,
    detect_divergence
)

from .signals import (
    SignalType,
    SignalGenerator,
    generate_trading_signals,
    get_latest_signal
)

__all__ = [
    # Moving Averages
    "calculate_sma",
    "calculate_ema",
    "calculate_wma",
    "calculate_all_ma",

    # Trend Indicators
    "calculate_macd",
    "calculate_bollinger",
    "calculate_adx",

    # Momentum Indicators
    "calculate_rsi",
    "calculate_kdj",
    "calculate_stochastic",
    "calculate_cci",

    # Volatility Indicators
    "calculate_atr",
    "calculate_volatility",

    # Volume Indicators
    "calculate_obv",
    "calculate_vwap",
    "calculate_mfi",

    # Comprehensive
    "calculate_all_indicators",

    # Helpers
    "detect_golden_cross",
    "detect_divergence",

    # Signals
    "SignalType",
    "SignalGenerator",
    "generate_trading_signals",
    "get_latest_signal",
]