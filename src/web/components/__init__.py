"""
Web 组件模块
Web Components Module

该模块提供 UI 组件，包括图表和表格。
This module provides UI components, including charts and tables.
"""

from .charts import (
    create_candlestick_chart,
    create_line_chart,
    create_volume_chart,
    create_technical_indicator_chart,
    create_performance_chart,
    create_pie_chart,
    create_heatmap
)

from .tables import (
    create_stock_table,
    create_metrics_row,
    create_stock_list_table,
    create_portfolio_table,
    create_trade_history_table,
    create_backtest_result_table,
    create_financial_table,
    create_factor_exposure_table,
    create_signal_table
)

__all__ = [
    # Charts
    "create_candlestick_chart",
    "create_line_chart",
    "create_volume_chart",
    "create_technical_indicator_chart",
    "create_performance_chart",
    "create_pie_chart",
    "create_heatmap",

    # Tables
    "create_stock_table",
    "create_metrics_row",
    "create_stock_list_table",
    "create_portfolio_table",
    "create_trade_history_table",
    "create_backtest_result_table",
    "create_financial_table",
    "create_factor_exposure_table",
    "create_signal_table",
]