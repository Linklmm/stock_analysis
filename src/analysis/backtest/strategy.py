"""
回测策略基类模块
Backtest Strategy Base Module

该模块定义了回测策略的抽象基类和常用策略实现。
This module defines abstract base class and common strategy implementations for backtesting.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from src.core.utils import logger


class Signal(Enum):
    """
    交易信号枚举
    Trading signal enumeration
    """
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class Position:
    """
    持仓信息
    Position information

    Attributes:
        code: 股票代码
        shares: 持仓数量
        cost: 成本价
        current_price: 当前价格
        market_value: 市值
    """
    code: str
    shares: float
    cost: float
    current_price: float = 0

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def profit_loss(self) -> float:
        return (self.current_price - self.cost) * self.shares

    @property
    def profit_loss_pct(self) -> float:
        return (self.current_price - self.cost) / self.cost if self.cost > 0 else 0


@dataclass
class Trade:
    """
    交易记录
    Trade record

    Attributes:
        datetime: 交易时间
        code: 股票代码
        direction: 方向 (buy/sell)
        shares: 数量
        price: 价格
        amount: 金额
        commission: 手续费
    """
    datetime: datetime
    code: str
    direction: str
    shares: float
    price: float
    amount: float
    commission: float


class BaseStrategy(ABC):
    """
    策略抽象基类
    Abstract base class for strategies

    所有回测策略必须实现此接口。
    All backtest strategies must implement this interface.

    Attributes:
        name: 策略名称
        params: 策略参数
    """

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        """
        初始化策略

        Args:
            name: 策略名称
            params: 策略参数
        """
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        Generate trading signals

        Args:
            data: 价格数据

        Returns:
            信号序列 (1: 买入, -1: 卖出, 0: 持有)
        """
        pass

    def on_bar(self, bar: pd.Series, position: Optional[Position]) -> Signal:
        """
        处理每根K线
        Handle each bar

        Args:
            bar: K线数据
            position: 当前持仓

        Returns:
            交易信号
        """
        # 默认实现使用 generate_signals
        # 子类可以重写此方法实现更复杂的逻辑
        pass

    def on_start(self):
        """策略开始时的初始化"""
        pass

    def on_end(self):
        """策略结束时的清理"""
        pass

    def get_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return self.params.copy()

    def set_params(self, **kwargs):
        """设置策略参数"""
        self.params.update(kwargs)


class BuyAndHoldStrategy(BaseStrategy):
    """
    买入持有策略
    Buy and Hold Strategy

    在开始时买入，持有到结束。
    Buy at the beginning and hold until the end.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("BuyAndHold", params)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信号"""
        signals = pd.Series(0, index=data.index)
        signals.iloc[0] = 1  # 第一天买入
        return signals


class MACrossStrategy(BaseStrategy):
    """
    均线交叉策略
    Moving Average Cross Strategy

    短期均线上穿长期均线买入，下穿卖出。
    Buy when short MA crosses above long MA, sell when crosses below.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            "short_period": 5,
            "long_period": 20
        }
        if params:
            default_params.update(params)
        super().__init__("MACross", default_params)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信号"""
        short_period = self.params["short_period"]
        long_period = self.params["long_period"]

        close = data["close"]

        # 计算均线
        short_ma = close.rolling(short_period).mean()
        long_ma = close.rolling(long_period).mean()

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 金叉
        golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        signals[golden_cross] = 1

        # 死叉
        death_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
        signals[death_cross] = -1

        return signals


class RSIStrategy(BaseStrategy):
    """
    RSI 策略
    RSI Strategy

    RSI 超卖买入，超买卖出。
    Buy when RSI is oversold, sell when overbought.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            "period": 14,
            "oversold": 30,
            "overbought": 70
        }
        if params:
            default_params.update(params)
        super().__init__("RSI", default_params)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信号"""
        from src.analysis.technical import calculate_rsi

        period = self.params["period"]
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]

        # 计算 RSI
        rsi_data = calculate_rsi(data, period)
        rsi = rsi_data["rsi"]

        # 生成信号
        signals = pd.Series(0, index=data.index)

        # 超卖买入
        signals[rsi < oversold] = 1

        # 超买卖出
        signals[rsi > overbought] = -1

        return signals


class MACDStrategy(BaseStrategy):
    """
    MACD 策略
    MACD Strategy

    MACD 上穿信号线买入，下穿卖出。
    Buy when MACD crosses above signal line, sell when crosses below.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
        if params:
            default_params.update(params)
        super().__init__("MACD", default_params)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信号"""
        from src.analysis.technical import calculate_macd

        macd_data = calculate_macd(data)

        signals = pd.Series(0, index=data.index)

        # 金叉
        golden_cross = (macd_data["macd"] > macd_data["signal"]) & \
                       (macd_data["macd"].shift(1) <= macd_data["signal"].shift(1))
        signals[golden_cross] = 1

        # 死叉
        death_cross = (macd_data["macd"] < macd_data["signal"]) & \
                      (macd_data["macd"].shift(1) >= macd_data["signal"].shift(1))
        signals[death_cross] = -1

        return signals


class BollingerBandsStrategy(BaseStrategy):
    """
    布林带策略
    Bollinger Bands Strategy

    价格触及下轨买入，触及上轨卖出。
    Buy when price touches lower band, sell when touches upper band.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            "period": 20,
            "std_dev": 2.0
        }
        if params:
            default_params.update(params)
        super().__init__("BollingerBands", default_params)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成信号"""
        from src.analysis.technical import calculate_bollinger

        period = self.params["period"]
        std_dev = self.params["std_dev"]

        boll_data = calculate_bollinger(data, period, std_dev)

        close = data["close"]
        signals = pd.Series(0, index=data.index)

        # 触及下轨买入
        touch_lower = close <= boll_data["lower"]
        signals[touch_lower] = 1

        # 触及上轨卖出
        touch_upper = close >= boll_data["upper"]
        signals[touch_upper] = -1

        return signals


class CompositeStrategy(BaseStrategy):
    """
    组合策略
    Composite Strategy

    组合多个策略的信号。
    Combine signals from multiple strategies.
    """

    def __init__(
        self,
        strategies: List[BaseStrategy],
        weights: Optional[List[float]] = None,
        threshold: float = 0.5
    ):
        """
        初始化组合策略

        Args:
            strategies: 策略列表
            weights: 权重列表
            threshold: 信号阈值
        """
        super().__init__("Composite", {
            "strategies": [s.name for s in strategies],
            "weights": weights,
            "threshold": threshold
        })

        self.strategies = strategies
        self.weights = weights or [1.0 / len(strategies)] * len(strategies)
        self.threshold = threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成组合信号"""
        signals_list = []

        for strategy in self.strategies:
            signals = strategy.generate_signals(data)
            signals_list.append(signals)

        # 加权组合
        combined = pd.DataFrame(signals_list).T
        combined = combined.apply(
            lambda row: sum(row * self.weights),
            axis=1
        )

        # 根据阈值生成最终信号
        final_signals = pd.Series(0, index=data.index)
        final_signals[combined >= self.threshold] = 1
        final_signals[combined <= -self.threshold] = -1

        return final_signals


# 策略注册表
STRATEGY_REGISTRY: Dict[str, type] = {
    "buy_and_hold": BuyAndHoldStrategy,
    "ma_cross": MACrossStrategy,
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
    "bollinger": BollingerBandsStrategy,
}


def create_strategy(name: str, params: Optional[Dict] = None) -> BaseStrategy:
    """
    创建策略的便捷函数
    Convenience function to create strategy

    Args:
        name: 策略名称
        params: 策略参数

    Returns:
        策略实例
    """
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"未知的策略: {name}，可用策略: {list(STRATEGY_REGISTRY.keys())}")

    return STRATEGY_REGISTRY[name](params)


def list_strategies() -> List[str]:
    """
    列出所有可用策略
    List all available strategies

    Returns:
        策略名称列表
    """
    return list(STRATEGY_REGISTRY.keys())