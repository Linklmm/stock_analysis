"""
表格组件模块
Table Components Module

该模块提供各种数据表格组件，
用于展示股票数据和分析结果。

This module provides various data table components
for displaying stock data and analysis results.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, List, Optional, Union

import pandas as pd
import numpy as np
import streamlit as st

from src.core.utils import format_number, format_percentage, format_money, format_volume


def create_stock_table(
    data: pd.DataFrame,
    title: str = None,
    show_index: bool = True,
    decimal: int = 2
) -> None:
    """
    创建股票数据表格
    Create stock data table

    Args:
        data: 股票数据
        title: 表格标题
        show_index: 是否显示索引
        decimal: 小数位数
    """
    if title:
        st.subheader(title)

    # 格式化数据
    formatted_data = data.copy()

    # 数值列格式化
    numeric_columns = formatted_data.select_dtypes(include=[np.number]).columns

    format_dict = {}
    for col in numeric_columns:
        if "price" in col.lower() or col in ["open", "high", "low", "close"]:
            format_dict[col] = f"{{:.{decimal}f}}"
        elif "volume" in col.lower():
            format_dict[col] = "{:,.0f}"
        elif "pct" in col.lower() or "rate" in col.lower() or "return" in col.lower():
            format_dict[col] = "{:.2%}"
        else:
            format_dict[col] = f"{{:.{decimal}f}}"

    st.dataframe(
        formatted_data.style.format(format_dict, na_rep="-"),
        use_container_width=True
    )


def create_metrics_row(
    metrics: Dict[str, Dict[str, Union[float, str]]],
    columns: int = 4
) -> None:
    """
    创建指标行
    Create metrics row

    Args:
        metrics: 指标字典 {名称: {value: 值, delta: 变化, help: 帮助文本}}
        columns: 列数
    """
    cols = st.columns(columns)

    for i, (name, info) in enumerate(metrics.items()):
        with cols[i % columns]:
            st.metric(
                label=name,
                value=info.get("value", "-"),
                delta=info.get("delta"),
                delta_color=info.get("delta_color", "normal"),
                help=info.get("help")
            )


def create_stock_list_table(
    stocks: pd.DataFrame,
    show_actions: bool = True
) -> None:
    """
    创建股票列表表格
    Create stock list table

    Args:
        stocks: 股票列表数据
        show_actions: 是否显示操作按钮
    """
    # 配置列
    column_config = {
        "code": st.column_config.TextColumn("代码", width="small"),
        "name": st.column_config.TextColumn("名称", width="medium"),
        "price": st.column_config.NumberColumn("价格", format="¥%.2f"),
        "change": st.column_config.NumberColumn("涨跌幅", format="%.2f%%"),
        "volume": st.column_config.NumberColumn("成交量", format="%d万"),
        "amount": st.column_config.NumberColumn("成交额", format="%.2f亿"),
    }

    if show_actions and "code" in stocks.columns:
        # 添加选择按钮列
        stocks["action"] = "选择"

    st.dataframe(
        stocks,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )


def create_portfolio_table(
    positions: pd.DataFrame,
    show_totals: bool = True
) -> None:
    """
    创建持仓表格
    Create portfolio table

    Args:
        positions: 持仓数据
        show_totals: 是否显示汇总
    """
    # 计算市值
    if "market_value" not in positions.columns and "shares" in positions.columns and "price" in positions.columns:
        positions["market_value"] = positions["shares"] * positions["price"]

    # 计算盈亏
    if "pnl" not in positions.columns and "cost" in positions.columns:
        positions["pnl"] = positions["market_value"] - positions["cost"] * positions["shares"]
        positions["pnl_pct"] = (positions["price"] - positions["cost"]) / positions["cost"]

    # 列配置
    column_config = {
        "code": st.column_config.TextColumn("代码"),
        "name": st.column_config.TextColumn("名称"),
        "shares": st.column_config.NumberColumn("持仓数量", format="%d"),
        "cost": st.column_config.NumberColumn("成本价", format="¥%.2f"),
        "price": st.column_config.NumberColumn("现价", format="¥%.2f"),
        "market_value": st.column_config.NumberColumn("市值", format="¥%.2f"),
        "pnl": st.column_config.NumberColumn("盈亏", format="¥%.2f"),
        "pnl_pct": st.column_config.NumberColumn("盈亏%", format="%.2f%%"),
    }

    st.dataframe(
        positions,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )

    # 显示汇总
    if show_totals:
        total_value = positions["market_value"].sum() if "market_value" in positions.columns else 0
        total_pnl = positions["pnl"].sum() if "pnl" in positions.columns else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("总市值", f"¥{total_value:,.2f}")

        with col2:
            st.metric("总盈亏", f"¥{total_pnl:,.2f}")

        with col3:
            if total_value > 0:
                total_pnl_pct = total_pnl / (total_value - total_pnl) * 100
                st.metric("总收益率", f"{total_pnl_pct:.2f}%")


def create_trade_history_table(
    trades: pd.DataFrame
) -> None:
    """
    创建交易历史表格
    Create trade history table

    Args:
        trades: 交易记录
    """
    column_config = {
        "datetime": st.column_config.DatetimeColumn("时间"),
        "code": st.column_config.TextColumn("代码"),
        "name": st.column_config.TextColumn("名称"),
        "direction": st.column_config.TextColumn("方向"),
        "price": st.column_config.NumberColumn("价格", format="¥%.2f"),
        "shares": st.column_config.NumberColumn("数量", format="%d"),
        "amount": st.column_config.NumberColumn("金额", format="¥%.2f"),
        "commission": st.column_config.NumberColumn("手续费", format="¥%.2f"),
    }

    st.dataframe(
        trades,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )


def create_backtest_result_table(
    results: Dict[str, float]
) -> None:
    """
    创建回测结果表格
    Create backtest result table

    Args:
        results: 回测结果字典
    """
    # 将结果转换为 DataFrame
    df = pd.DataFrame([
        {"指标": k, "值": v} for k, v in results.items()
    ])

    st.dataframe(
        df,
        column_config={
            "指标": st.column_config.TextColumn("指标", width="medium"),
            "值": st.column_config.TextColumn("值", width="medium")
        },
        use_container_width=True,
        hide_index=True
    )


def create_financial_table(
    data: pd.DataFrame,
    title: str = None
) -> None:
    """
    创建财务数据表格
    Create financial data table

    Args:
        data: 财务数据
        title: 表格标题
    """
    if title:
        st.subheader(title)

    # 格式化大数字
    formatted = data.copy()

    for col in formatted.columns:
        if formatted[col].dtype in [np.float64, np.int64]:
            # 检查数值大小，决定单位
            max_val = formatted[col].abs().max()
            if max_val >= 1e8:
                formatted[col] = formatted[col] / 1e8
                col_name = f"{col}(亿)"
            elif max_val >= 1e4:
                formatted[col] = formatted[col] / 1e4
                col_name = f"{col}(万)"
            else:
                col_name = col

            formatted = formatted.rename(columns={col: col_name})

    st.dataframe(
        formatted.style.format("{:.2f}", na_rep="-"),
        use_container_width=True
    )


def create_factor_exposure_table(
    exposures: pd.DataFrame
) -> None:
    """
    创建因子暴露表格
    Create factor exposure table

    Args:
        exposures: 因子暴露数据
    """
    # 添加颜色编码
    def color_exposure(val):
        """根据正负值着色"""
        if pd.isna(val):
            return ""
        color = "#dc3545" if val < 0 else "#28a745"
        return f"color: {color}"

    styled = exposures.style.applymap(
        color_exposure,
        subset=exposures.select_dtypes(include=[np.number]).columns
    ).format("{:.4f}", na_rep="-")

    st.dataframe(styled, use_container_width=True)


def create_signal_table(
    signals: pd.DataFrame,
    latest_only: bool = True
) -> None:
    """
    创建信号表格
    Create signal table

    Args:
        signals: 信号数据
        latest_only: 是否只显示最新信号
    """
    if latest_only:
        signals = signals.tail(10)

    # 添加信号强度颜色
    def color_signal(val):
        """根据信号着色"""
        if val == "买入":
            return "background-color: #d4edda"
        elif val == "卖出":
            return "background-color: #f8d7da"
        else:
            return ""

    styled = signals.style.applymap(
        color_signal,
        subset=["signal"] if "signal" in signals.columns else []
    )

    st.dataframe(styled, use_container_width=True)