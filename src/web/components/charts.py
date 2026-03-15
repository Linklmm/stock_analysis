"""
图表组件模块
Chart Components Module

该模块提供各种可视化图表组件，
用于展示股票数据和分析结果。

This module provides various visualization chart components
for displaying stock data and analysis results.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.core.utils import format_percentage, format_volume


def create_candlestick_chart(
    data: pd.DataFrame,
    title: str = "K线图",
    show_volume: bool = True,
    show_ma: bool = True,
    ma_periods: List[int] = None
) -> go.Figure:
    """
    创建 K 线图（蜡烛图）
    Create candlestick chart

    Args:
        data: 行情数据，需包含 open, high, low, close, volume 列
        title: 图表标题
        show_volume: 是否显示成交量
        show_ma: 是否显示均线
        ma_periods: 均线周期列表

    Returns:
        Plotly Figure 对象
    """
    if ma_periods is None:
        ma_periods = [5, 10, 20]

    # 确保数据有正确的索引
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)

    # 统一成交量列名（兼容 vol 和 volume）
    if 'vol' in data.columns and 'volume' not in data.columns:
        data['volume'] = data['vol']
    elif 'volume' in data.columns and 'vol' not in data.columns:
        data['vol'] = data['volume']

    # 创建子图
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=("价格", "成交量")
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # 添加 K 线
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name="K线",
            increasing_line_color="#28a745",
            decreasing_line_color="#dc3545"
        ),
        row=1, col=1
    )

    # 添加均线
    if show_ma:
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        for i, period in enumerate(ma_periods):
            ma = data["close"].rolling(period).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=ma,
                    mode="lines",
                    name=f"MA{period}",
                    line=dict(color=colors[i % len(colors)], width=1)
                ),
                row=1, col=1
            )

    # 添加成交量
    if show_volume:
        # 成交量柱状图，根据涨跌显示不同颜色
        colors = np.where(
            data["close"] >= data["open"],
            "#28a745",  # 涨
            "#dc3545"   # 跌
        )

        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["volume"],
                name="成交量",
                marker_color=colors,
                opacity=0.8
            ),
            row=2, col=1
        )

    # 更新布局
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=600 if show_volume else 400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_rangeslider_visible=False
    )

    # 更新轴标签
    fig.update_yaxes(title_text="价格", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="成交量", row=2, col=1)

    return fig


def create_line_chart(
    data: pd.DataFrame,
    y_column: str = "close",
    title: str = "价格走势",
    show_range: bool = True,
    show_ma: bool = True,
    ma_period: int = 20
) -> go.Figure:
    """
    创建折线图
    Create line chart

    Args:
        data: 数据
        y_column: Y 轴列名
        title: 图表标题
        show_range: 是否显示价格区间
        show_ma: 是否显示均线
        ma_period: 均线周期

    Returns:
        Plotly Figure 对象
    """
    # 确保数据有正确的索引
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)

    fig = go.Figure()

    # 主线
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data[y_column],
        mode="lines",
        name=y_column.capitalize(),
        line=dict(color="#1f77b4", width=2)
    ))

    # 价格区间（高低点）
    if show_range and "high" in data.columns and "low" in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["high"],
            mode="lines",
            name="最高价",
            line=dict(color="#28a745", width=1, dash="dot"),
            opacity=0.5
        ))

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["low"],
            mode="lines",
            name="最低价",
            line=dict(color="#dc3545", width=1, dash="dot"),
            opacity=0.5
        ))

    # 均线
    if show_ma:
        ma = data[y_column].rolling(ma_period).mean()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=ma,
            mode="lines",
            name=f"MA{ma_period}",
            line=dict(color="#ff7f0e", width=1)
        ))

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="价格",
        template="plotly_white",
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_volume_chart(
    data: pd.DataFrame,
    title: str = "成交量"
) -> go.Figure:
    """
    创建成交量图表
    Create volume chart

    Args:
        data: 数据，需包含 volume 列
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    # 确保数据有正确的索引
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)

    # 根据涨跌显示不同颜色
    colors = np.where(
        data["close"] >= data["open"],
        "#28a745",
        "#dc3545"
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data.index,
        y=data["volume"],
        name="成交量",
        marker_color=colors,
        opacity=0.8
    ))

    # 添加成交量均线
    ma5 = data["volume"].rolling(5).mean()
    ma10 = data["volume"].rolling(10).mean()

    fig.add_trace(go.Scatter(
        x=data.index,
        y=ma5,
        mode="lines",
        name="MA5",
        line=dict(color="#1f77b4", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=ma10,
        mode="lines",
        name="MA10",
        line=dict(color="#ff7f0e", width=1)
    ))

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="成交量",
        template="plotly_white",
        height=300,
        showlegend=True
    )

    return fig


def create_technical_indicator_chart(
    data: pd.DataFrame,
    indicator: str,
    title: str = None
) -> go.Figure:
    """
    创建技术指标图表
    Create technical indicator chart

    Args:
        data: 数据
        indicator: 指标名称 ("macd", "rsi", "kdj", "boll")
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    from src.analysis.technical.indicators import (
        calculate_macd, calculate_rsi, calculate_kdj, calculate_bollinger
    )

    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)

    if indicator.lower() == "macd":
        # MACD 指标
        macd_data = calculate_macd(data)
        title = title or "MACD 指标"

        fig = make_subplots(rows=2, cols=1, row_heights=[0.5, 0.5])

        # 价格和 BOLL
        fig.add_trace(
            go.Scatter(x=data.index, y=data["close"], name="收盘价"),
            row=1, col=1
        )

        # MACD
        fig.add_trace(
            go.Bar(
                x=macd_data.index,
                y=macd_data["macd_hist"],
                name="MACD Histogram",
                marker_color=np.where(macd_data["macd_hist"] >= 0, "#28a745", "#dc3545")
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(x=macd_data.index, y=macd_data["macd"], name="MACD"),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(x=macd_data.index, y=macd_data["signal"], name="Signal"),
            row=2, col=1
        )

    elif indicator.lower() == "rsi":
        # RSI 指标
        rsi_data = calculate_rsi(data)
        title = title or "RSI 指标"

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=rsi_data.index,
            y=rsi_data["rsi"],
            name="RSI",
            line=dict(color="#1f77b4", width=2)
        ))

        # 添加超买超卖线
        fig.add_hline(y=70, line_dash="dash", line_color="#dc3545", annotation_text="超买")
        fig.add_hline(y=30, line_dash="dash", line_color="#28a745", annotation_text="超卖")
        fig.add_hline(y=50, line_dash="dot", line_color="gray")

    elif indicator.lower() == "kdj":
        # KDJ 指标
        kdj_data = calculate_kdj(data)
        title = title or "KDJ 指标"

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=kdj_data.index, y=kdj_data["k"], name="K",
            line=dict(color="#1f77b4", width=2)
        ))

        fig.add_trace(go.Scatter(
            x=kdj_data.index, y=kdj_data["d"], name="D",
            line=dict(color="#ff7f0e", width=2)
        ))

        fig.add_trace(go.Scatter(
            x=kdj_data.index, y=kdj_data["j"], name="J",
            line=dict(color="#2ca02c", width=2)
        ))

        # 超买超卖线
        fig.add_hline(y=80, line_dash="dash", line_color="#dc3545")
        fig.add_hline(y=20, line_dash="dash", line_color="#28a745")

    elif indicator.lower() == "boll":
        # 布林带
        boll_data = calculate_bollinger(data)
        title = title or "布林带"

        fig = go.Figure()

        # 价格
        fig.add_trace(go.Scatter(
            x=data.index, y=data["close"], name="收盘价",
            line=dict(color="#1f77b4", width=2)
        ))

        # 上轨
        fig.add_trace(go.Scatter(
            x=boll_data.index, y=boll_data["upper"], name="上轨",
            line=dict(color="#dc3545", width=1)
        ))

        # 中轨
        fig.add_trace(go.Scatter(
            x=boll_data.index, y=boll_data["middle"], name="中轨",
            line=dict(color="#ff7f0e", width=1)
        ))

        # 下轨
        fig.add_trace(go.Scatter(
            x=boll_data.index, y=boll_data["lower"], name="下轨",
            line=dict(color="#28a745", width=1)
        ))

        # 填充区域
        fig.add_trace(go.Scatter(
            x=boll_data.index,
            y=boll_data["upper"],
            fill=None,
            mode="lines",
            line_color="rgba(0,0,0,0)",
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=boll_data.index,
            y=boll_data["lower"],
            fill="tonexty",
            mode="lines",
            line_color="rgba(0,0,0,0)",
            fillcolor="rgba(31, 119, 180, 0.1)",
            showlegend=False
        ))

    else:
        raise ValueError(f"不支持的指标: {indicator}")

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        template="plotly_white",
        height=400,
        showlegend=True
    )

    return fig


def create_performance_chart(
    returns: pd.Series,
    benchmark: pd.Series = None,
    title: str = "累计收益"
) -> go.Figure:
    """
    创建收益表现图表
    Create performance chart

    Args:
        returns: 收益率序列
        benchmark: 基准收益率序列
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    # 计算累计收益
    cumulative = (1 + returns).cumprod() - 1

    fig = go.Figure()

    # 策略收益
    fig.add_trace(go.Scatter(
        x=cumulative.index,
        y=cumulative * 100,  # 转换为百分比
        mode="lines",
        name="策略",
        line=dict(color="#1f77b4", width=2)
    ))

    # 基准收益
    if benchmark is not None:
        benchmark_cumulative = (1 + benchmark).cumprod() - 1
        fig.add_trace(go.Scatter(
            x=benchmark_cumulative.index,
            y=benchmark_cumulative * 100,
            mode="lines",
            name="基准",
            line=dict(color="#ff7f0e", width=2, dash="dash")
        ))

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="累计收益 (%)",
        template="plotly_white",
        height=400,
        showlegend=True,
        hovermode="x unified"
    )

    # 添加零线
    fig.add_hline(y=0, line_dash="dot", line_color="gray")

    return fig


def create_pie_chart(
    data: Dict[str, float],
    title: str = "资产配置"
) -> go.Figure:
    """
    创建饼图
    Create pie chart

    Args:
        data: 数据字典 {标签: 值}
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure(data=[go.Pie(
        labels=list(data.keys()),
        values=list(data.values()),
        hole=0.3,
        textinfo="label+percent",
        textposition="outside"
    )])

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=400
    )

    return fig


def create_heatmap(
    data: pd.DataFrame,
    title: str = "相关性热力图"
) -> go.Figure:
    """
    创建热力图
    Create heatmap

    Args:
        data: 相关性矩阵
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale="RdBu",
        zmid=0,
        text=data.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10}
    ))

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=500,
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )

    return fig