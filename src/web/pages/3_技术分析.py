"""
技术分析页面
Technical Analysis Page

该页面提供技术指标可视化和交易信号分析功能。
This page provides technical indicator visualization and trading signal analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st

# 页面配置（必须在所有 st 命令之前）
st.set_page_config(
    page_title="技术分析",
    page_icon="📈",
    layout="wide"
)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.utils import normalize_stock_code, parse_date
from src.analysis.technical.indicators import (
    calculate_all_indicators,
    calculate_macd,
    calculate_rsi,
    calculate_kdj,
    calculate_bollinger,
    calculate_atr
)
from src.analysis.technical.signals import (
    SignalGenerator,
    generate_trading_signals,
    get_latest_signal
)
from src.web.components.charts import (
    create_candlestick_chart,
    create_technical_indicator_chart,
    create_line_chart
)
from src.web.components.tables import create_signal_table


def get_display_name(ts_code: str, name: str) -> str:
    """
    获取用于显示的股票名称（优先中文）
    """
    if name and '.' not in name and name != ts_code:
        return name
    return ts_code


def main():
    """技术分析主页面"""

    # 页面标题
    st.markdown(
        '<p class="main-header">📈 技术分析</p>',
        unsafe_allow_html=True
    )

    # 初始化 session state
    if "ta_stock_code" not in st.session_state:
        st.session_state.ta_stock_code = st.session_state.get("selected_stock", "000001.SZ")
    if "ta_data" not in st.session_state:
        st.session_state.ta_data = None
    if "ta_last_analyzed" not in st.session_state:
        st.session_state.ta_last_analyzed = None
    if "ta_trigger_analyze" not in st.session_state:
        st.session_state.ta_trigger_analyze = False

    # 侧边栏配置
    with st.sidebar:
        st.subheader("分析配置")

        # 自选股选择
        st.markdown("**从自选股选择:**")
        try:
            from src.data.database import db_manager
            watchlist = db_manager.get_watchlist()
        except Exception:
            watchlist = []

        if watchlist:
            # 自选股下拉选择
            watch_options = {}
            for item in watchlist:
                display_name = get_display_name(item['ts_code'], item.get('name'))
                watch_options[f"{display_name} ({item['ts_code']})"] = item['ts_code']

            selected_watch = st.selectbox(
                "选择自选股",
                options=["-- 请选择 --"] + list(watch_options.keys()),
                key="ta_watchlist_select",
                label_visibility="collapsed"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("分析", key="ta_load_watch", type="primary", use_container_width=True):
                    if selected_watch != "-- 请选择 --":
                        new_code = watch_options[selected_watch]
                        st.session_state.ta_stock_code = new_code
                        st.session_state.ta_data = None  # 清除旧数据
                        st.session_state.ta_last_analyzed = None
                        st.session_state.ta_trigger_analyze = True  # 触发分析
                        st.rerun()
            with col2:
                if st.button("清空", key="ta_clear_watch", use_container_width=True):
                    st.session_state.ta_stock_code = "000001.SZ"
                    st.session_state.ta_data = None
                    st.session_state.ta_last_analyzed = None
                    st.session_state.ta_trigger_analyze = False
                    st.rerun()

            st.divider()
        else:
            st.caption("暂无自选股")
            st.divider()

        # 股票代码输入
        st.markdown("**或输入股票代码:**")
        input_code = st.text_input(
            "股票代码",
            value=st.session_state.ta_stock_code,
            placeholder="如: 000001 或 600519",
            key="ta_code_input"
        )

        # 如果输入的代码变化，更新状态
        if input_code != st.session_state.ta_stock_code:
            st.session_state.ta_stock_code = input_code
            st.session_state.ta_data = None
            st.session_state.ta_last_analyzed = None

        # 日期范围
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=(datetime.now() - timedelta(days=365)).date(),
                key="ta_start_date"
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now().date(),
                key="ta_end_date"
            )

        # 指标选择
        st.subheader("选择指标")
        show_ma = st.checkbox("移动平均线", value=True)
        show_macd = st.checkbox("MACD", value=True)
        show_rsi = st.checkbox("RSI", value=True)
        show_kdj = st.checkbox("KDJ", value=True)
        show_boll = st.checkbox("布林带", value=True)
        show_volume = st.checkbox("成交量", value=True)

        # 分析按钮
        analyze_btn = st.button("开始分析", type="primary", use_container_width=True)

    # 获取当前股票代码
    current_stock = st.session_state.ta_stock_code

    # 判断是否需要分析
    need_analyze = analyze_btn or st.session_state.ta_trigger_analyze

    # 主内容区域
    if need_analyze:
        # 清除旧数据，强制重新获取
        st.session_state.ta_data = None
        st.session_state.ta_trigger_analyze = False  # 重置触发标志
        analyze_technical(
            stock_code=current_stock,
            start_date=str(start_date),
            end_date=str(end_date),
            show_ma=show_ma,
            show_macd=show_macd,
            show_rsi=show_rsi,
            show_kdj=show_kdj,
            show_boll=show_boll,
            show_volume=show_volume
        )
    elif st.session_state.ta_data is not None and st.session_state.ta_last_analyzed == current_stock:
        # 显示已缓存的数据（只有当缓存的股票和当前一致时）
        analyze_technical(
            stock_code=current_stock,
            start_date=str(start_date),
            end_date=str(end_date),
            show_ma=show_ma,
            show_macd=show_macd,
            show_rsi=show_rsi,
            show_kdj=show_kdj,
            show_boll=show_boll,
            show_volume=show_volume,
            use_cached=True
        )
    else:
        # 显示说明
        show_instructions()


def analyze_technical(
    stock_code: str,
    start_date: str,
    end_date: str,
    show_ma: bool = True,
    show_macd: bool = True,
    show_rsi: bool = True,
    show_kdj: bool = True,
    show_boll: bool = True,
    show_volume: bool = True,
    use_cached: bool = False
):
    """
    执行技术分析

    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        show_ma: 是否显示均线
        show_macd: 是否显示 MACD
        show_rsi: 是否显示 RSI
        show_kdj: 是否显示 KDJ
        show_boll: 是否显示布林带
        show_volume: 是否显示成交量
        use_cached: 是否使用缓存数据
    """
    data_with_indicators = None

    if use_cached and st.session_state.get("ta_data") is not None:
        # 使用缓存数据
        data_with_indicators = st.session_state.ta_data
    else:
        # 重新获取数据
        with st.spinner("正在分析..."):
            try:
                # 获取数据
                data = get_stock_data(stock_code, start_date, end_date)

                if data is None or data.empty:
                    st.error("未获取到数据，请检查股票代码和日期范围")
                    return

                # 计算技术指标
                data_with_indicators = calculate_all_indicators(data)
                st.session_state["ta_data"] = data_with_indicators
                st.session_state["ta_last_analyzed"] = stock_code

            except Exception as e:
                st.error(f"分析失败: {e}")
                st.exception(e)
                return

    # 显示分析结果
    data = data_with_indicators

    # 股票信息概览
    show_stock_overview(data, stock_code)

    # K 线图
    st.subheader("K 线图")

    ma_periods = []
    if show_ma:
        ma_periods = [5, 10, 20, 60]

    fig = create_candlestick_chart(
        data,
        title=f"{stock_code} K线图",
        show_volume=show_volume,
        show_ma=show_ma,
        ma_periods=ma_periods
    )

    st.plotly_chart(fig, use_container_width=True)

    # 技术指标
    st.subheader("技术指标")

    # 使用标签页组织指标
    tabs = []
    tab_names = []
    if show_macd:
        tab_names.append("MACD")
    if show_rsi:
        tab_names.append("RSI")
    if show_kdj:
        tab_names.append("KDJ")
    if show_boll:
        tab_names.append("布林带")

    if tab_names:
        tabs = st.tabs(tab_names)

        tab_idx = 0
        if show_macd:
            with tabs[tab_idx]:
                show_macd_indicator(data)
            tab_idx += 1

        if show_rsi:
            with tabs[tab_idx]:
                show_rsi_indicator(data)
            tab_idx += 1

        if show_kdj:
            with tabs[tab_idx]:
                show_kdj_indicator(data)
            tab_idx += 1

        if show_boll:
            with tabs[tab_idx]:
                show_bollinger_indicator(data)
            tab_idx += 1

    # 交易信号
    st.divider()
    st.subheader("交易信号分析")

    show_trading_signals(data)


def get_stock_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取股票真实数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        股票数据
    """
    from src.core.utils import normalize_stock_code
    from src.data.realtime import get_stock_history

    try:
        # 标准化股票代码
        code = normalize_stock_code(stock_code)

        # 使用 AkShare 获取真实数据
        data = get_stock_history(
            code=code,
            start_date=start_date,
            end_date=end_date
        )

        if data is not None and not data.empty:
            # 列名兼容处理：vol -> volume
            if 'vol' in data.columns and 'volume' not in data.columns:
                data['volume'] = data['vol']
            return data

    except Exception as e:
        st.error(f"获取数据失败: {e}")

    return None


def show_stock_overview(data: pd.DataFrame, stock_code: str):
    """
    显示股票概览

    Args:
        data: 数据
        stock_code: 股票代码
    """
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else latest

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        change_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
        st.metric(
            "最新价",
            f"¥{latest['close']:.2f}",
            f"{change_pct:+.2f}%",
            delta_color="normal" if change_pct >= 0 else "inverse"
        )

    with col2:
        st.metric("最高价", f"¥{latest['high']:.2f}")

    with col3:
        st.metric("最低价", f"¥{latest['low']:.2f}")

    with col4:
        st.metric("成交量", f"{latest['volume']/1e4:.0f}万")

    with col5:
        st.metric("振幅", f"{(latest['high'] - latest['low']) / latest['low'] * 100:.2f}%")


def show_macd_indicator(data: pd.DataFrame):
    """显示 MACD 指标"""
    try:
        fig = create_technical_indicator_chart(data, "macd")
        st.plotly_chart(fig, use_container_width=True)

        # MACD 分析
        macd_data = calculate_macd(data)
        latest = macd_data.iloc[-1]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("MACD", f"{latest['macd']:.4f}")
        with col2:
            st.metric("Signal", f"{latest['signal']:.4f}")
        with col3:
            st.metric("Histogram", f"{latest['macd_hist']:.4f}")

        # 信号解读
        if latest['macd'] > latest['signal']:
            st.success("📈 MACD 位于信号线上方，多头趋势")
        else:
            st.warning("📉 MACD 位于信号线下方，空头趋势")

    except Exception as e:
        st.error(f"MACD 指标计算失败: {e}")


def show_rsi_indicator(data: pd.DataFrame):
    """显示 RSI 指标"""
    try:
        fig = create_technical_indicator_chart(data, "rsi")
        st.plotly_chart(fig, use_container_width=True)

        # RSI 分析
        rsi_data = calculate_rsi(data)
        latest_rsi = rsi_data["rsi"].iloc[-1]

        st.metric("RSI(14)", f"{latest_rsi:.2f}")

        # 信号解读
        if latest_rsi > 70:
            st.warning("⚠️ RSI 超过 70，处于超买区域，可能回调")
        elif latest_rsi < 30:
            st.success("💡 RSI 低于 30，处于超卖区域，可能反弹")
        else:
            st.info(f"RSI 在正常区间 (30-70)")

    except Exception as e:
        st.error(f"RSI 指标计算失败: {e}")


def show_kdj_indicator(data: pd.DataFrame):
    """显示 KDJ 指标"""
    try:
        fig = create_technical_indicator_chart(data, "kdj")
        st.plotly_chart(fig, use_container_width=True)

        # KDJ 分析
        kdj_data = calculate_kdj(data)
        latest = kdj_data.iloc[-1]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("K", f"{latest['k']:.2f}")
        with col2:
            st.metric("D", f"{latest['d']:.2f}")
        with col3:
            st.metric("J", f"{latest['j']:.2f}")

        # 信号解读
        if latest['k'] > latest['d']:
            st.success("📈 K 线在 D 线上方，多头信号")
        else:
            st.warning("📉 K 线在 D 线下方，空头信号")

    except Exception as e:
        st.error(f"KDJ 指标计算失败: {e}")


def show_bollinger_indicator(data: pd.DataFrame):
    """显示布林带指标"""
    try:
        fig = create_technical_indicator_chart(data, "boll")
        st.plotly_chart(fig, use_container_width=True)

        # 布林带分析
        boll_data = calculate_bollinger(data)
        latest = boll_data.iloc[-1]
        price = data["close"].iloc[-1]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("上轨", f"¥{latest['upper']:.2f}")
        with col2:
            st.metric("中轨", f"¥{latest['middle']:.2f}")
        with col3:
            st.metric("下轨", f"¥{latest['lower']:.2f}")

        # 信号解读
        if price >= latest['upper']:
            st.warning("⚠️ 价格触及上轨，可能回调")
        elif price <= latest['lower']:
            st.success("💡 价格触及下轨，可能反弹")
        else:
            st.info("价格在布林带内运行")

    except Exception as e:
        st.error(f"布林带指标计算失败: {e}")


def show_trading_signals(data: pd.DataFrame):
    """
    显示交易信号

    Args:
        data: 数据
    """
    try:
        # 生成信号
        signal_data = generate_trading_signals(data)

        # 最新信号
        latest_signal = get_latest_signal(signal_data)

        # 显示综合信号
        signal_value = latest_signal["signal"]
        signal_desc = SignalGenerator().get_signal_description(signal_value)

        if signal_value >= 1:
            st.success(f"🟢 **综合信号**: {signal_desc}")
        elif signal_value <= -1:
            st.error(f"🔴 **综合信号**: {signal_desc}")
        else:
            st.info(f"⚪ **综合信号**: {signal_desc}")

        # 各指标信号得分
        col1, col2, col3, col4, col5 = st.columns(5)

        signals = [
            ("MA", latest_signal["ma_signal"]),
            ("MACD", latest_signal["macd_signal"]),
            ("RSI", latest_signal["rsi_signal"]),
            ("KDJ", latest_signal["kdj_signal"]),
            ("BOLL", latest_signal["bollinger_signal"])
        ]

        for i, (name, value) in enumerate(signals):
            with [col1, col2, col3, col4, col5][i]:
                if value > 0:
                    st.metric(name, f"{value:.2f}", delta="买入", delta_color="normal")
                elif value < 0:
                    st.metric(name, f"{value:.2f}", delta="卖出", delta_color="inverse")
                else:
                    st.metric(name, f"{value:.2f}", delta="持有")

        # 信号历史
        with st.expander("查看信号历史"):
            signal_history = signal_data[["close", "final_signal", "composite_signal"]].tail(20)
            signal_history.columns = ["收盘价", "综合信号", "综合得分"]
            st.dataframe(signal_history, use_container_width=True)

    except Exception as e:
        st.error(f"交易信号计算失败: {e}")


def show_instructions():
    """显示使用说明"""
    st.info("""
    ### 📊 技术分析功能说明

    本页面提供以下技术分析功能：

    **趋势指标**
    - 移动平均线 (MA): 判断价格趋势方向
    - MACD: 判断趋势强度和转折点
    - 布林带: 判断价格波动区间

    **动量指标**
    - RSI: 判断超买超卖状态
    - KDJ: 判断买卖时机

    **交易信号**
    - 综合多种指标生成买卖信号
    - 提供信号强度评分

    请在左侧输入股票代码和日期范围，选择需要分析的指标。
    """)


if __name__ == "__main__":
    main()