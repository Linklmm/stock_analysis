"""
技术指标计算模块
Technical Indicators Calculation Module

该模块提供各种常用技术指标的计算函数，
包括趋势指标、动量指标、波动率指标等。

This module provides calculation functions for various common technical indicators,
including trend indicators, momentum indicators, volatility indicators, etc.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np

from src.core.exceptions import TechnicalAnalysisError
from src.core.utils import logger
from config.settings import TECHNICAL_INDICATORS


# ==================== 移动平均线 / Moving Averages ====================

def calculate_ma(data: pd.Series, period: int, ma_type: str = "sma") -> pd.Series:
    """
    计算移动平均线（通用接口）
    Calculate Moving Average (generic interface)

    Args:
        data: 价格数据
        period: 周期
        ma_type: 移动平均类型 ("sma", "ema", "wma")

    Returns:
        MA 序列
    """
    if ma_type.lower() == "sma":
        return calculate_sma(data, period)
    elif ma_type.lower() == "ema":
        return calculate_ema(data, period)
    elif ma_type.lower() == "wma":
        return calculate_wma(data, period)
    else:
        return calculate_sma(data, period)


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """
    计算简单移动平均线
    Calculate Simple Moving Average

    SMA = (P1 + P2 + ... + Pn) / n

    Args:
        data: 价格数据
        period: 周期

    Returns:
        SMA 序列
    """
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线
    Calculate Exponential Moving Average

    EMA = α * Price + (1 - α) * EMA_prev
    α = 2 / (n + 1)

    Args:
        data: 价格数据
        period: 周期

    Returns:
        EMA 序列
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_wma(data: pd.Series, period: int) -> pd.Series:
    """
    计算加权移动平均线
    Calculate Weighted Moving Average

    WMA = (n*P1 + (n-1)*P2 + ... + 1*Pn) / (n + (n-1) + ... + 1)

    Args:
        data: 价格数据
        period: 周期

    Returns:
        WMA 序列
    """
    weights = np.arange(1, period + 1)
    return data.rolling(window=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(),
        raw=True
    )


def calculate_all_ma(
    data: pd.DataFrame,
    price_col: str = "close",
    periods: List[int] = None,
    ma_type: str = "sma"
) -> pd.DataFrame:
    """
    计算多条移动平均线
    Calculate multiple moving averages

    Args:
        data: 价格数据
        price_col: 价格列名
        periods: 周期列表
        ma_type: 移动平均类型 ("sma", "ema", "wma")

    Returns:
        包含均线的 DataFrame
    """
    if periods is None:
        periods = TECHNICAL_INDICATORS["ma_periods"]

    result = data.copy()

    for period in periods:
        if ma_type.lower() == "sma":
            result[f"ma_{period}"] = calculate_sma(data[price_col], period)
        elif ma_type.lower() == "ema":
            result[f"ema_{period}"] = calculate_ema(data[price_col], period)
        elif ma_type.lower() == "wma":
            result[f"wma_{period}"] = calculate_wma(data[price_col], period)

    return result


# ==================== 趋势指标 / Trend Indicators ====================

def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    price_col: str = "close"
) -> pd.DataFrame:
    """
    计算 MACD 指标
    Calculate MACD indicator

    MACD = EMA(12) - EMA(26)
    Signal = EMA(MACD, 9)
    Histogram = MACD - Signal

    Args:
        data: 价格数据
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        price_col: 价格列名

    Returns:
        包含 MACD, Signal, Histogram 的 DataFrame
    """
    price = data[price_col]

    # 计算快慢 EMA
    ema_fast = calculate_ema(price, fast_period)
    ema_slow = calculate_ema(price, slow_period)

    # MACD 线
    macd = ema_fast - ema_slow

    # 信号线
    signal = calculate_ema(macd, signal_period)

    # MACD 柱
    histogram = macd - signal

    result = pd.DataFrame({
        "macd": macd,
        "signal": signal,
        "macd_hist": histogram
    }, index=data.index)

    return result


def calculate_bollinger(
    data: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = "close"
) -> pd.DataFrame:
    """
    计算布林带
    Calculate Bollinger Bands

    中轨 = SMA(n)
    上轨 = 中轨 + k * σ
    下轨 = 中轨 - k * σ

    Args:
        data: 价格数据
        period: 周期
        std_dev: 标准差倍数
        price_col: 价格列名

    Returns:
        包含上轨、中轨、下轨的 DataFrame
    """
    price = data[price_col]

    # 中轨（SMA）
    middle = calculate_sma(price, period)

    # 标准差
    std = price.rolling(window=period).std()

    # 上轨和下轨
    upper = middle + std_dev * std
    lower = middle - std_dev * std

    # 带宽
    bandwidth = (upper - lower) / middle

    # %B
    percent_b = (price - lower) / (upper - lower)

    result = pd.DataFrame({
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "bandwidth": bandwidth,
        "percent_b": percent_b
    }, index=data.index)

    return result


def calculate_adx(
    data: pd.DataFrame,
    period: int = 14
) -> pd.DataFrame:
    """
    计算平均趋向指标
    Calculate Average Directional Index

    Args:
        data: 价格数据（需包含 high, low, close）
        period: 周期

    Returns:
        包含 ADX, +DI, -DI 的 DataFrame
    """
    high = data["high"]
    low = data["low"]
    close = data["close"]

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # Smoothed values
    atr = calculate_ema(pd.Series(tr), period)
    plus_di = 100 * calculate_ema(pd.Series(plus_dm), period) / atr
    minus_di = 100 * calculate_ema(pd.Series(minus_dm), period) / atr

    # DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = calculate_ema(dx, period)

    result = pd.DataFrame({
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di
    }, index=data.index)

    return result


# ==================== 动量指标 / Momentum Indicators ====================

def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
    price_col: str = "close"
) -> pd.DataFrame:
    """
    计算相对强弱指数
    Calculate Relative Strength Index

    RSI = 100 - 100 / (1 + RS)
    RS = Average Gain / Average Loss

    Args:
        data: 价格数据
        period: 周期
        price_col: 价格列名

    Returns:
        包含 RSI 的 DataFrame
    """
    price = data[price_col]

    # 价格变化
    delta = price.diff()

    # 分离涨跌
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    # 平均涨跌
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # RS
    rs = avg_gain / avg_loss

    # RSI
    rsi = 100 - (100 / (1 + rs))

    result = pd.DataFrame({"rsi": rsi}, index=data.index)

    return result


def calculate_kdj(
    data: pd.DataFrame,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> pd.DataFrame:
    """
    计算 KDJ 指标
    Calculate KDJ indicator

    RSV = (Close - Min(Low, n)) / (Max(High, n) - Min(Low, n)) * 100
    K = SMA(RSV, m1)
    D = SMA(K, m2)
    J = 3 * K - 2 * D

    Args:
        data: 价格数据（需包含 high, low, close）
        n: RSV 周期
        m1: K 线平滑周期
        m2: D 线平滑周期

    Returns:
        包含 K, D, J 的 DataFrame
    """
    low_min = data["low"].rolling(window=n).min()
    high_max = data["high"].rolling(window=n).max()

    # RSV
    rsv = (data["close"] - low_min) / (high_max - low_min) * 100

    # K, D, J
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()
    d = k.ewm(alpha=1/m2, adjust=False).mean()
    j = 3 * k - 2 * d

    result = pd.DataFrame({
        "k": k,
        "d": d,
        "j": j,
        "rsv": rsv
    }, index=data.index)

    return result


def calculate_stochastic(
    data: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
    smooth_k: int = 3
) -> pd.DataFrame:
    """
    计算随机指标
    Calculate Stochastic Oscillator

    %K = (Close - Min(Low, n)) / (Max(High, n) - Min(Low, n)) * 100
    %D = SMA(%K, m)

    Args:
        data: 价格数据
        k_period: K 周期
        d_period: D 周期
        smooth_k: K 平滑周期

    Returns:
        包含 %K, %D 的 DataFrame
    """
    low_min = data["low"].rolling(window=k_period).min()
    high_max = data["high"].rolling(window=k_period).max()

    # %K
    k = (data["close"] - low_min) / (high_max - low_min) * 100
    k = k.rolling(window=smooth_k).mean()

    # %D
    d = k.rolling(window=d_period).mean()

    result = pd.DataFrame({
        "stoch_k": k,
        "stoch_d": d
    }, index=data.index)

    return result


def calculate_cci(
    data: pd.DataFrame,
    period: int = 20
) -> pd.DataFrame:
    """
    计算顺势指标
    Calculate Commodity Channel Index

    CCI = (TP - SMA(TP, n)) / (0.015 * Mean Deviation)

    Args:
        data: 价格数据
        period: 周期

    Returns:
        包含 CCI 的 DataFrame
    """
    # Typical Price
    tp = (data["high"] + data["low"] + data["close"]) / 3

    # SMA of TP
    sma_tp = tp.rolling(window=period).mean()

    # Mean Deviation
    mad = tp.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean()
    )

    # CCI
    cci = (tp - sma_tp) / (0.015 * mad)

    result = pd.DataFrame({"cci": cci}, index=data.index)

    return result


# ==================== 波动率指标 / Volatility Indicators ====================

def calculate_atr(
    data: pd.DataFrame,
    period: int = 14
) -> pd.DataFrame:
    """
    计算平均真实波幅
    Calculate Average True Range

    TR = max(H-L, |H-Cp|, |L-Cp|)
    ATR = SMA(TR, n)

    Args:
        data: 价格数据
        period: 周期

    Returns:
        包含 ATR 的 DataFrame
    """
    high = data["high"]
    low = data["low"]
    close = data["close"]

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR
    atr = tr.rolling(window=period).mean()

    result = pd.DataFrame({
        "atr": atr,
        "tr": tr
    }, index=data.index)

    return result


def calculate_volatility(
    data: pd.DataFrame,
    period: int = 20,
    price_col: str = "close"
) -> pd.DataFrame:
    """
    计算历史波动率
    Calculate Historical Volatility

    σ = std(daily_returns) * sqrt(252)

    Args:
        data: 价格数据
        period: 周期
        price_col: 价格列名

    Returns:
        包含波动率的 DataFrame
    """
    price = data[price_col]

    # 日收益率
    returns = price.pct_change()

    # 滚动波动率（年化）
    volatility = returns.rolling(window=period).std() * np.sqrt(252)

    result = pd.DataFrame({
        "volatility": volatility,
        "returns": returns
    }, index=data.index)

    return result


# ==================== 成交量指标 / Volume Indicators ====================

def calculate_obv(data: pd.DataFrame) -> pd.Series:
    """
    计算能量潮指标
    Calculate On-Balance Volume

    OBV = OBV_prev + volume (if close > close_prev)
    OBV = OBV_prev - volume (if close < close_prev)

    Args:
        data: 价格数据（需包含 close, volume）

    Returns:
        OBV 序列
    """
    close = data["close"]
    volume = data["volume"]

    # 价格变化方向
    direction = np.sign(close.diff())

    # OBV
    obv = (direction * volume).cumsum()

    return obv


def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """
    计算成交量加权平均价
    Calculate Volume Weighted Average Price

    VWAP = Σ(Price * Volume) / Σ(Volume)

    Args:
        data: 价格数据（需包含 high, low, close, volume）

    Returns:
        VWAP 序列
    """
    # Typical Price
    tp = (data["high"] + data["low"] + data["close"]) / 3

    # VWAP
    vwap = (tp * data["volume"]).cumsum() / data["volume"].cumsum()

    return vwap


def calculate_mfi(
    data: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    计算资金流量指标
    Calculate Money Flow Index

    MFI = 100 - 100 / (1 + Money Flow Ratio)

    Args:
        data: 价格数据
        period: 周期

    Returns:
        MFI 序列
    """
    # Typical Price
    tp = (data["high"] + data["low"] + data["close"]) / 3

    # Money Flow
    mf = tp * data["volume"]

    # Positive and Negative Money Flow
    positive_mf = mf.where(tp > tp.shift(1), 0)
    negative_mf = mf.where(tp < tp.shift(1), 0)

    # Money Flow Ratio
    positive_sum = positive_mf.rolling(window=period).sum()
    negative_sum = negative_mf.rolling(window=period).sum()

    mfr = positive_sum / negative_sum

    # MFI
    mfi = 100 - (100 / (1 + mfr))

    return mfi


# ==================== 综合指标计算 / Comprehensive Indicator Calculation ====================

def calculate_all_indicators(
    data: pd.DataFrame,
    include_volume: bool = True
) -> pd.DataFrame:
    """
    计算所有常用技术指标
    Calculate all common technical indicators

    Args:
        data: 价格数据
        include_volume: 是否包含成交量指标

    Returns:
        包含所有指标的 DataFrame
    """
    result = data.copy()

    try:
        # 移动平均线
        result = calculate_all_ma(result)

        # MACD
        macd = calculate_macd(result)
        result = pd.concat([result, macd], axis=1)

        # 布林带
        boll = calculate_bollinger(result)
        result = pd.concat([result, boll], axis=1)

        # RSI
        rsi = calculate_rsi(result)
        result = pd.concat([result, rsi], axis=1)

        # KDJ
        kdj = calculate_kdj(result)
        result = pd.concat([result, kdj], axis=1)

        # ATR
        atr = calculate_atr(result)
        result = pd.concat([result, atr], axis=1)

        # 波动率
        vol = calculate_volatility(result)
        result = pd.concat([result, vol], axis=1)

        # 成交量指标
        if include_volume:
            result["obv"] = calculate_obv(result)
            result["vwap"] = calculate_vwap(result)
            result["mfi"] = calculate_mfi(result)

        logger.info(f"计算了 {len(result.columns) - len(data.columns)} 个技术指标")

    except Exception as e:
        logger.error(f"计算技术指标失败: {e}")
        raise TechnicalAnalysisError(
            indicator="all",
            message="计算技术指标失败",
            details=str(e)
        )

    return result


# ==================== 辅助函数 / Helper Functions ====================

def detect_golden_cross(data: pd.DataFrame, fast_col: str, slow_col: str) -> pd.Series:
    """
    检测金叉信号
    Detect golden cross signals

    金叉：快线上穿慢线
    Golden cross: fast line crosses above slow line

    Args:
        data: 数据
        fast_col: 快线列名
        slow_col: 慢线列名

    Returns:
        信号序列 (1: 金叉, -1: 死叉, 0: 无信号)
    """
    fast = data[fast_col]
    slow = data[slow_col]

    # 金叉：快线上穿慢线
    golden_cross = (fast > slow) & (fast.shift(1) <= slow.shift(1))

    # 死叉：快线下穿慢线
    death_cross = (fast < slow) & (fast.shift(1) >= slow.shift(1))

    signal = pd.Series(0, index=data.index)
    signal[golden_cross] = 1
    signal[death_cross] = -1

    return signal


def detect_divergence(
    price: pd.Series,
    indicator: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    检测背离信号
    Detect divergence signals

    顶背离：价格创新高，指标未创新高
    底背离：价格创新低，指标未创新低

    Args:
        price: 价格序列
        indicator: 指标序列
        period: 检测周期

    Returns:
        信号序列 (1: 底背离, -1: 顶背离, 0: 无信号)
    """
    signal = pd.Series(0, index=price.index)

    for i in range(period, len(price)):
        # 获取区间数据
        price_range = price.iloc[i-period:i+1]
        indicator_range = indicator.iloc[i-period:i+1]

        # 检测顶背离
        if price_range.iloc[-1] == price_range.max():
            if indicator_range.iloc[-1] < indicator_range.max():
                signal.iloc[i] = -1

        # 检测底背离
        elif price_range.iloc[-1] == price_range.min():
            if indicator_range.iloc[-1] > indicator_range.min():
                signal.iloc[i] = 1

    return signal