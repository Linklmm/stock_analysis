"""
交易信号生成模块
Trading Signal Generation Module

该模块提供各种交易信号的生成功能，
包括技术指标信号、趋势信号等。

This module provides trading signal generation functionality,
including technical indicator signals, trend signals, etc.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

import pandas as pd
import numpy as np

from src.core.utils import logger
from src.analysis.technical.indicators import (
    calculate_macd, calculate_rsi, calculate_kdj,
    calculate_bollinger, calculate_ma, calculate_atr
)


class SignalType(Enum):
    """
    信号类型枚举
    Signal type enumeration
    """
    BUY = 1          # 买入信号 / Buy signal
    SELL = -1        # 卖出信号 / Sell signal
    HOLD = 0         # 持有/观望 / Hold/Watch
    STRONG_BUY = 2   # 强买入 / Strong buy
    STRONG_SELL = -2 # 强卖出 / Strong sell


class SignalGenerator:
    """
    交易信号生成器
    Trading signal generator

    综合多种技术指标生成交易信号。
    Generate trading signals based on multiple technical indicators.

    Attributes:
        config: 配置参数
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信号生成器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 默认参数
        self.ma_periods = self.config.get("ma_periods", [5, 10, 20, 60])
        self.rsi_oversold = self.config.get("rsi_oversold", 30)
        self.rsi_overbought = self.config.get("rsi_overbought", 70)
        self.kdj_oversold = self.config.get("kdj_oversold", 20)
        self.kdj_overbought = self.config.get("kdj_overbought", 80)

    def generate_signals(
        self,
        data: pd.DataFrame,
        methods: List[str] = None
    ) -> pd.DataFrame:
        """
        生成综合交易信号
        Generate comprehensive trading signals

        Args:
            data: 价格数据
            methods: 信号方法列表

        Returns:
            包含信号的 DataFrame
        """
        if methods is None:
            methods = ["ma", "macd", "rsi", "kdj", "bollinger"]

        result = data.copy()
        signals = pd.DataFrame(index=data.index)

        # 生成各种信号
        if "ma" in methods:
            signals["ma_signal"] = self.ma_signal(data)

        if "macd" in methods:
            signals["macd_signal"] = self.macd_signal(data)

        if "rsi" in methods:
            signals["rsi_signal"] = self.rsi_signal(data)

        if "kdj" in methods:
            signals["kdj_signal"] = self.kdj_signal(data)

        if "bollinger" in methods:
            signals["bollinger_signal"] = self.bollinger_signal(data)

        # 综合信号
        signals["composite_signal"] = signals.mean(axis=1)

        # 离散化综合信号
        signals["final_signal"] = self._discretize_signal(signals["composite_signal"])

        result = pd.concat([result, signals], axis=1)

        return result

    def ma_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        移动平均线信号
        Moving average signal

        策略：
        - 价格在均线上方为多头
        - 短期均线上穿长期均线为买入
        - 短期均线下穿长期均线为卖出

        Args:
            data: 价格数据

        Returns:
            信号序列
        """
        close = data["close"]

        # 计算均线
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()

        signal = pd.Series(0, index=data.index)

        # 金叉/死叉信号
        golden_cross = (ma5 > ma10) & (ma5.shift(1) <= ma10.shift(1))
        death_cross = (ma5 < ma10) & (ma5.shift(1) >= ma10.shift(1))

        signal[golden_cross] = 1
        signal[death_cross] = -1

        # 趋势判断
        uptrend = (close > ma5) & (ma5 > ma10) & (ma10 > ma20)
        downtrend = (close < ma5) & (ma5 < ma10) & (ma10 < ma20)

        signal[uptrend] = signal[uptrend].clip(lower=0.5)
        signal[downtrend] = signal[downtrend].clip(upper=-0.5)

        return signal

    def macd_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        MACD 信号
        MACD signal

        策略：
        - MACD 上穿信号线为买入
        - MACD 下穿信号线为卖出
        - 零轴上方为多头，下方为空头

        Args:
            data: 价格数据

        Returns:
            信号序列
        """
        macd_data = calculate_macd(data)

        signal = pd.Series(0, index=data.index)

        # MACD 上穿/下穿信号线
        golden_cross = (macd_data["macd"] > macd_data["signal"]) & \
                       (macd_data["macd"].shift(1) <= macd_data["signal"].shift(1))
        death_cross = (macd_data["macd"] < macd_data["signal"]) & \
                      (macd_data["macd"].shift(1) >= macd_data["signal"].shift(1))

        signal[golden_cross] = 1
        signal[death_cross] = -1

        # 零轴判断
        above_zero = macd_data["macd"] > 0
        below_zero = macd_data["macd"] < 0

        # 柱状图变化趋势
        histogram_increasing = macd_data["macd_hist"] > macd_data["macd_hist"].shift(1)
        histogram_decreasing = macd_data["macd_hist"] < macd_data["macd_hist"].shift(1)

        # 增强信号
        signal[above_zero & histogram_increasing] = signal[above_zero & histogram_increasing].clip(lower=0.5)
        signal[below_zero & histogram_decreasing] = signal[below_zero & histogram_decreasing].clip(upper=-0.5)

        return signal

    def rsi_signal(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        RSI 信号
        RSI signal

        策略：
        - RSI < 30 超卖，买入信号
        - RSI > 70 超买，卖出信号
        - RSI 从下向上穿过 50，买入信号

        Args:
            data: 价格数据
            period: RSI 周期

        Returns:
            信号序列
        """
        rsi_data = calculate_rsi(data, period)
        rsi = rsi_data["rsi"]

        signal = pd.Series(0, index=data.index)

        # 超卖区域
        oversold = rsi < self.rsi_oversold
        signal[oversold] = 1

        # 超买区域
        overbought = rsi > self.rsi_overbought
        signal[overbought] = -1

        # 穿越 50 线
        cross_up_50 = (rsi > 50) & (rsi.shift(1) <= 50)
        cross_down_50 = (rsi < 50) & (rsi.shift(1) >= 50)

        signal[cross_up_50] = 0.5
        signal[cross_down_50] = -0.5

        return signal

    def kdj_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        KDJ 信号
        KDJ signal

        策略：
        - K 上穿 D，买入信号
        - K 下穿 D，卖出信号
        - J < 0 或 K, D < 20，超买
        - J > 100 或 K, D > 80，超卖

        Args:
            data: 价格数据

        Returns:
            信号序列
        """
        kdj_data = calculate_kdj(data)

        signal = pd.Series(0, index=data.index)

        # K 上穿/下穿 D
        golden_cross = (kdj_data["k"] > kdj_data["d"]) & \
                       (kdj_data["k"].shift(1) <= kdj_data["d"].shift(1))
        death_cross = (kdj_data["k"] < kdj_data["d"]) & \
                      (kdj_data["k"].shift(1) >= kdj_data["d"].shift(1))

        signal[golden_cross] = 1
        signal[death_cross] = -1

        # 超卖区域
        oversold = (kdj_data["k"] < self.kdj_oversold) & \
                   (kdj_data["d"] < self.kdj_oversold)
        signal[oversold] = signal[oversold].clip(lower=1)

        # 超买区域
        overbought = (kdj_data["k"] > self.kdj_overbought) & \
                     (kdj_data["d"] > self.kdj_overbought)
        signal[overbought] = signal[overbought].clip(upper=-1)

        # J 值极端
        j_extreme_low = kdj_data["j"] < 0
        j_extreme_high = kdj_data["j"] > 100

        signal[j_extreme_low] = signal[j_extreme_low].clip(lower=1.5)
        signal[j_extreme_high] = signal[j_extreme_high].clip(upper=-1.5)

        return signal

    def bollinger_signal(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        布林带信号
        Bollinger Bands signal

        策略：
        - 价格触及下轨，买入信号
        - 价格触及上轨，卖出信号
        - 价格从中轨向上突破，买入信号

        Args:
            data: 价格数据
            period: 周期

        Returns:
            信号序列
        """
        boll_data = calculate_bollinger(data, period)
        close = data["close"]

        signal = pd.Series(0, index=data.index)

        # 触及下轨
        touch_lower = close <= boll_data["lower"]
        signal[touch_lower] = 1

        # 触及上轨
        touch_upper = close >= boll_data["upper"]
        signal[touch_upper] = -1

        # 从中轨向上突破
        cross_up_middle = (close > boll_data["middle"]) & \
                          (close.shift(1) <= boll_data["middle"].shift(1))
        signal[cross_up_middle] = 0.5

        # 从中轨向下突破
        cross_down_middle = (close < boll_data["middle"]) & \
                            (close.shift(1) >= boll_data["middle"].shift(1))
        signal[cross_down_middle] = -0.5

        # 带宽收窄（可能即将突破）
        bandwidth_narrow = boll_data["bandwidth"] < boll_data["bandwidth"].rolling(20).quantile(0.2)
        signal[bandwidth_narrow] = 0  # 观望

        return signal

    def volume_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        成交量信号
        Volume signal

        策略：
        - 放量上涨，买入信号
        - 放量下跌，卖出信号

        Args:
            data: 价格数据

        Returns:
            信号序列
        """
        close = data["close"]
        volume = data["volume"]

        # 成交量均线
        vol_ma = volume.rolling(20).mean()

        # 价格变化
        price_change = close.pct_change()

        signal = pd.Series(0, index=data.index)

        # 放量上涨
        volume_increase = volume > vol_ma * 1.5
        price_up = price_change > 0

        signal[volume_increase & price_up] = 1

        # 放量下跌
        price_down = price_change < 0
        signal[volume_increase & price_down] = -1

        return signal

    def trend_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        趋势信号
        Trend signal

        使用 ATR 判断趋势强度

        Args:
            data: 价格数据

        Returns:
            信号序列
        """
        close = data["close"]
        atr_data = calculate_atr(data)
        atr = atr_data["atr"]

        signal = pd.Series(0, index=data.index)

        # 使用 ATR 作为趋势过滤器
        high_channel = close.rolling(20).max() - atr * 2
        low_channel = close.rolling(20).min() + atr * 2

        # 突破上通道
        break_up = close > high_channel.shift(1)
        signal[break_up] = 1

        # 突破下通道
        break_down = close < low_channel.shift(1)
        signal[break_down] = -1

        return signal

    def _discretize_signal(self, signal: pd.Series) -> pd.Series:
        """
        离散化信号
        Discretize signal

        将连续信号转换为离散信号

        Args:
            signal: 连续信号

        Returns:
            离散信号
        """
        result = pd.Series(0, index=signal.index)

        result[signal >= 0.8] = 2   # 强买入
        result[(signal >= 0.3) & (signal < 0.8)] = 1  # 买入
        result[(signal > -0.3) & (signal < 0.3)] = 0  # 持有
        result[(signal <= -0.3) & (signal > -0.8)] = -1  # 卖出
        result[signal <= -0.8] = -2  # 强卖出

        return result

    def get_signal_description(self, signal_value: int) -> str:
        """
        获取信号描述
        Get signal description

        Args:
            signal_value: 信号值

        Returns:
            信号描述
        """
        descriptions = {
            2: "强烈买入 - 多个指标发出买入信号",
            1: "买入 - 建议买入",
            0: "持有/观望 - 无明确信号",
            -1: "卖出 - 建议卖出",
            -2: "强烈卖出 - 多个指标发出卖出信号"
        }
        return descriptions.get(signal_value, "未知信号")


def generate_trading_signals(
    data: pd.DataFrame,
    methods: List[str] = None
) -> pd.DataFrame:
    """
    生成交易信号的便捷函数
    Convenience function to generate trading signals

    Args:
        data: 价格数据
        methods: 信号方法列表

    Returns:
        包含信号的 DataFrame
    """
    generator = SignalGenerator()
    return generator.generate_signals(data, methods)


def get_latest_signal(data: pd.DataFrame) -> Dict:
    """
    获取最新信号
    Get latest signal

    Args:
        data: 价格数据（包含信号）

    Returns:
        最新信号信息
    """
    if "final_signal" not in data.columns:
        data = generate_trading_signals(data)

    latest = data.iloc[-1]

    return {
        "signal": int(latest.get("final_signal", 0)),
        "composite_score": latest.get("composite_signal", 0),
        "ma_signal": latest.get("ma_signal", 0),
        "macd_signal": latest.get("macd_signal", 0),
        "rsi_signal": latest.get("rsi_signal", 0),
        "kdj_signal": latest.get("kdj_signal", 0),
        "bollinger_signal": latest.get("bollinger_signal", 0)
    }