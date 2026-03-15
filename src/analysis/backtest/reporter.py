"""
回测报告生成模块
Backtest Report Generation Module

该模块提供回测报告的生成和可视化功能。
This module provides backtest report generation and visualization functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from src.analysis.backtest.executor import BacktestResult
from src.core.utils import logger


class BacktestReporter:
    """
    回测报告生成器
    Backtest Report Generator

    生成回测报告和分析图表。
    Generate backtest reports and analysis charts.

    Attributes:
        result: 回测结果
    """

    def __init__(self, result: BacktestResult):
        """
        初始化报告生成器

        Args:
            result: 回测结果
        """
        self.result = result

    def generate_summary(self) -> Dict[str, Any]:
        """
        生成摘要
        Generate summary

        Returns:
            摘要字典
        """
        return {
            "策略名称": self.result.strategy_name,
            "回测区间": f"{self.result.start_date.strftime('%Y-%m-%d')} ~ {self.result.end_date.strftime('%Y-%m-%d')}",
            "初始资金": f"¥{self.result.initial_capital:,.2f}",
            "最终资金": f"¥{self.result.final_capital:,.2f}",
            "总收益率": f"{self.result.total_return * 100:.2f}%",
            "年化收益率": f"{self.result.annual_return * 100:.2f}%",
            "最大回撤": f"{self.result.max_drawdown * 100:.2f}%",
            "夏普比率": f"{self.result.sharpe_ratio:.2f}",
            "交易次数": len(self.result.trades)
        }

    def generate_trade_table(self) -> pd.DataFrame:
        """
        生成交易记录表
        Generate trade table

        Returns:
            交易记录 DataFrame
        """
        if not self.result.trades:
            return pd.DataFrame()

        records = []
        for trade in self.result.trades:
            records.append({
                "日期": trade.datetime.strftime("%Y-%m-%d"),
                "股票代码": trade.code,
                "方向": "买入" if trade.direction == "buy" else "卖出",
                "数量": trade.shares,
                "价格": f"¥{trade.price:.2f}",
                "金额": f"¥{trade.amount:,.2f}",
                "手续费": f"¥{trade.commission:.2f}"
            })

        return pd.DataFrame(records)

    def generate_metrics_table(self) -> pd.DataFrame:
        """
        生成指标表
        Generate metrics table

        Returns:
            指标 DataFrame
        """
        metrics = self.result.metrics or {}

        records = [
            {"指标": "总收益率", "值": f"{metrics.get('total_return', 0) * 100:.2f}%"},
            {"指标": "年化收益率", "值": f"{metrics.get('annual_return', 0) * 100:.2f}%"},
            {"指标": "最大回撤", "值": f"{metrics.get('max_drawdown', 0) * 100:.2f}%"},
            {"指标": "夏普比率", "值": f"{metrics.get('sharpe_ratio', 0):.2f}"},
            {"指标": "年化波动率", "值": f"{metrics.get('volatility', 0) * 100:.2f}%"},
        ]

        return pd.DataFrame(records)

    def plot_equity_curve(self):
        """
        绘制资金曲线
        Plot equity curve

        Returns:
            Plotly Figure
        """
        import plotly.graph_objects as go

        fig = go.Figure()

        # 资金曲线
        fig.add_trace(go.Scatter(
            x=self.result.equity_curve.index,
            y=self.result.equity_curve.values,
            mode="lines",
            name="策略净值",
            line=dict(color="#1f77b4", width=2)
        ))

        # 基准（如果有的话）
        fig.add_trace(go.Scatter(
            x=self.result.equity_curve.index,
            y=[self.result.initial_capital] * len(self.result.equity_curve),
            mode="lines",
            name="初始资金",
            line=dict(color="gray", width=1, dash="dash")
        ))

        fig.update_layout(
            title="资金曲线",
            xaxis_title="日期",
            yaxis_title="净值",
            template="plotly_white",
            height=400,
            showlegend=True
        )

        return fig

    def plot_drawdown(self):
        """
        绘制回撤曲线
        Plot drawdown curve

        Returns:
            Plotly Figure
        """
        import plotly.graph_objects as go

        equity = self.result.equity_curve
        cumulative = equity / equity.iloc[0]
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode="lines",
            name="回撤",
            fill="tozeroy",
            line=dict(color="#dc3545", width=1)
        ))

        fig.update_layout(
            title="回撤曲线",
            xaxis_title="日期",
            yaxis_title="回撤 (%)",
            template="plotly_white",
            height=300
        )

        return fig

    def plot_returns_distribution(self):
        """
        绘制收益分布
        Plot returns distribution

        Returns:
            Plotly Figure
        """
        import plotly.graph_objects as go

        returns = self.result.equity_curve.pct_change().dropna() * 100

        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name="日收益率",
            marker_color="#1f77b4",
            opacity=0.7
        ))

        fig.update_layout(
            title="日收益率分布",
            xaxis_title="日收益率 (%)",
            yaxis_title="频数",
            template="plotly_white",
            height=300
        )

        return fig

    def generate_report(self) -> str:
        """
        生成文本报告
        Generate text report

        Returns:
            报告文本
        """
        summary = self.generate_summary()

        report = f"""
========================================
        回测报告
========================================

策略名称: {summary['策略名称']}
回测区间: {summary['回测区间']}

----------------------------------------
         收益指标
----------------------------------------
初始资金: {summary['初始资金']}
最终资金: {summary['最终资金']}
总收益率: {summary['总收益率']}
年化收益率: {summary['年化收益率']}

----------------------------------------
         风险指标
----------------------------------------
最大回撤: {summary['最大回撤']}
夏普比率: {summary['夏普比率']}

----------------------------------------
         交易统计
----------------------------------------
交易次数: {summary['交易次数']}

========================================
"""

        return report

    def export_to_excel(self, filepath: str):
        """
        导出到 Excel
        Export to Excel

        Args:
            filepath: 文件路径
        """
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # 摘要
            summary = self.generate_summary()
            pd.DataFrame([summary]).T.to_excel(writer, sheet_name="摘要")

            # 指标
            metrics = self.generate_metrics_table()
            metrics.to_excel(writer, sheet_name="指标", index=False)

            # 交易记录
            trades = self.generate_trade_table()
            if not trades.empty:
                trades.to_excel(writer, sheet_name="交易记录", index=False)

            # 资金曲线
            equity = self.result.equity_curve.to_frame("净值")
            equity.to_excel(writer, sheet_name="资金曲线")

        logger.info(f"报告已导出到: {filepath}")


def create_report(result: BacktestResult) -> BacktestReporter:
    """
    创建报告的便捷函数
    Convenience function to create report

    Args:
        result: 回测结果

    Returns:
        报告生成器
    """
    return BacktestReporter(result)