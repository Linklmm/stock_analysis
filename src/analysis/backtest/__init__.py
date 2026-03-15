"""回测模块"""

from .strategy import (
    BaseStrategy,
    Signal,
    Position,
    Trade,
    BuyAndHoldStrategy,
    MACrossStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    CompositeStrategy,
    create_strategy,
    list_strategies,
    STRATEGY_REGISTRY
)

from .executor import (
    BacktestExecutor,
    BacktestResult,
    run_backtest
)

from .reporter import (
    BacktestReporter,
    create_report
)

__all__ = [
    # Strategy
    "BaseStrategy",
    "Signal",
    "Position",
    "Trade",
    "BuyAndHoldStrategy",
    "MACrossStrategy",
    "RSIStrategy",
    "MACDStrategy",
    "BollingerBandsStrategy",
    "CompositeStrategy",
    "create_strategy",
    "list_strategies",
    "STRATEGY_REGISTRY",

    # Executor
    "BacktestExecutor",
    "BacktestResult",
    "run_backtest",

    # Reporter
    "BacktestReporter",
    "create_report",
]