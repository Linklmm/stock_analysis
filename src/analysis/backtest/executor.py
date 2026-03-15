"""
回测执行器模块
Backtest Executor Module

该模块提供回测执行功能，模拟策略运行。
This module provides backtest execution functionality, simulating strategy runs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

from src.analysis.backtest.strategy import BaseStrategy, Signal, Position, Trade, create_strategy
from src.core.utils import logger
from config.settings import TRADING_CONFIG


@dataclass
class BacktestResult:
    """
    回测结果
    Backtest result

    Attributes:
        strategy_name: 策略名称
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        final_capital: 最终资金
        total_return: 总收益率
        annual_return: 年化收益率
        max_drawdown: 最大回撤
        sharpe_ratio: 夏普比率
        trades: 交易记录
        equity_curve: 资金曲线
    """
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Trade]
    equity_curve: pd.Series
    metrics: Dict[str, float] = None


class BacktestExecutor:
    """
    回测执行器
    Backtest Executor

    执行策略回测，计算收益和风险指标。
    Execute strategy backtest, calculate return and risk metrics.

    Attributes:
        initial_capital: 初始资金
        commission_rate: 手续费率
        stamp_duty_rate: 印花税率
        slippage: 滑点
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化回测执行器

        Args:
            config: 配置参数
        """
        config = config or {}

        self.initial_capital = config.get("initial_capital", TRADING_CONFIG.initial_capital)
        self.commission_rate = config.get("commission_rate", TRADING_CONFIG.commission_rate)
        self.stamp_duty_rate = config.get("stamp_duty_rate", TRADING_CONFIG.stamp_duty_rate)
        self.slippage = config.get("slippage", TRADING_CONFIG.slippage)
        self.min_commission = config.get("min_commission", TRADING_CONFIG.min_commission)

    def run(
        self,
        data: pd.DataFrame,
        strategy: Union[str, BaseStrategy],
        strategy_params: Optional[Dict] = None
    ) -> BacktestResult:
        """
        执行回测
        Execute backtest

        Args:
            data: 价格数据
            strategy: 策略名称或策略实例
            strategy_params: 策略参数

        Returns:
            回测结果
        """
        # 准备策略
        if isinstance(strategy, str):
            strategy = create_strategy(strategy, strategy_params)

        logger.info(f"开始回测策略: {strategy.name}")

        # 策略初始化
        strategy.on_start()

        # 生成信号
        signals = strategy.generate_signals(data)

        # 执行模拟交易
        result = self._simulate_trading(data, signals, strategy.name)

        # 策略结束
        strategy.on_end()

        return result

    def _simulate_trading(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        strategy_name: str
    ) -> BacktestResult:
        """
        模拟交易
        Simulate trading

        Args:
            data: 价格数据
            signals: 交易信号
            strategy_name: 策略名称

        Returns:
            回测结果
        """
        # 初始化
        cash = self.initial_capital
        position: Optional[Position] = None
        trades: List[Trade] = []
        equity_curve = []

        # 遍历数据
        for i, (date, row) in enumerate(data.iterrows()):
            price = row["close"]
            signal = signals.iloc[i]

            # 执行交易
            if signal == 1 and position is None:
                # 买入
                shares, amount, commission = self._calculate_buy(cash, price)
                if shares > 0:
                    position = Position(
                        code=row.get("code", "STOCK"),
                        shares=shares,
                        cost=price * (1 + self.slippage)
                    )
                    cash -= amount + commission
                    trades.append(Trade(
                        datetime=date,
                        code=position.code,
                        direction="buy",
                        shares=shares,
                        price=price,
                        amount=amount,
                        commission=commission
                    ))

            elif signal == -1 and position is not None:
                # 卖出
                shares = position.shares
                amount = shares * price * (1 - self.slippage)
                commission = self._calculate_commission(amount, is_sell=True)

                cash += amount - commission
                trades.append(Trade(
                    datetime=date,
                    code=position.code,
                    direction="sell",
                    shares=shares,
                    price=price,
                    amount=amount,
                    commission=commission
                ))
                position = None

            # 计算当前净值
            if position is not None:
                position.current_price = price
                total_value = cash + position.market_value
            else:
                total_value = cash

            equity_curve.append(total_value)

        # 最后如果还持仓，按收盘价清仓
        if position is not None:
            price = data["close"].iloc[-1]
            shares = position.shares
            amount = shares * price
            commission = self._calculate_commission(amount, is_sell=True)
            cash += amount - commission
            position = None

        # 创建资金曲线
        equity_series = pd.Series(equity_curve, index=data.index)

        # 计算绩效指标
        metrics = self._calculate_metrics(equity_series)

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital,
            final_capital=cash,
            total_return=metrics["total_return"],
            annual_return=metrics["annual_return"],
            max_drawdown=metrics["max_drawdown"],
            sharpe_ratio=metrics["sharpe_ratio"],
            trades=trades,
            equity_curve=equity_series,
            metrics=metrics
        )

    def _calculate_buy(
        self,
        cash: float,
        price: float
    ) -> tuple:
        """
        计算买入参数
        Calculate buy parameters

        Args:
            cash: 可用现金
            price: 价格

        Returns:
            (股数, 金额, 手续费)
        """
        # 考虑滑点
        buy_price = price * (1 + self.slippage)

        # 计算可买股数（按手为单位，1手=100股）
        max_shares = int(cash / (buy_price * 1.0003))  # 预留手续费
        shares = (max_shares // 100) * 100  # 向下取整到100股

        if shares <= 0:
            return 0, 0, 0

        amount = shares * buy_price
        commission = self._calculate_commission(amount, is_sell=False)

        return shares, amount, commission

    def _calculate_commission(self, amount: float, is_sell: bool = False) -> float:
        """
        计算手续费
        Calculate commission

        Args:
            amount: 成交金额
            is_sell: 是否卖出

        Returns:
            手续费
        """
        # 佣金
        commission = amount * self.commission_rate
        commission = max(commission, self.min_commission)

        # 印花税（仅卖出）
        if is_sell:
            commission += amount * self.stamp_duty_rate

        return commission

    def _calculate_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """
        计算绩效指标
        Calculate performance metrics

        Args:
            equity_curve: 资金曲线

        Returns:
            绩效指标字典
        """
        # 收益率
        returns = equity_curve.pct_change().dropna()

        # 总收益率
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)

        # 年化收益率
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())

        # 夏普比率
        if returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 其他指标
        win_rate = 0
        profit_loss_ratio = 0

        return {
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe_ratio),
            "volatility": float(returns.std() * np.sqrt(252)),
            "win_rate": float(win_rate),
            "profit_loss_ratio": float(profit_loss_ratio)
        }


def run_backtest(
    data: pd.DataFrame,
    strategy: Union[str, BaseStrategy],
    **kwargs
) -> BacktestResult:
    """
    执行回测的便捷函数
    Convenience function to run backtest

    Args:
        data: 价格数据
        strategy: 策略

    Returns:
        回测结果
    """
    executor = BacktestExecutor(kwargs)
    return executor.run(data, strategy, kwargs.get("strategy_params"))