"""
财报分析页面
Financial Report Analysis Page

该页面提供股票财报数据分析功能。
This page provides stock financial report analysis functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st

# 页面配置
st.set_page_config(
    page_title="财报分析",
    page_icon="📊",
    layout="wide"
)

import pandas as pd
import numpy as np
from datetime import datetime

from src.data.financial_report import get_financial_data, _financial_provider


def get_display_name(ts_code: str, name: str) -> str:
    """获取用于显示的股票名称"""
    if name and '.' not in name and name != ts_code:
        return name
    return ts_code


def main():
    """财报分析主页面"""

    # 页面标题
    st.markdown(
        '<p class="main-header">📊 财报分析</p>',
        unsafe_allow_html=True
    )

    # 初始化 session state
    if "fr_stock_code" not in st.session_state:
        st.session_state.fr_stock_code = st.session_state.get("selected_stock", "000001.SZ")
    if "fr_data" not in st.session_state:
        st.session_state.fr_data = None
    if "fr_trigger" not in st.session_state:
        st.session_state.fr_trigger = False

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
            watch_options = {}
            for item in watchlist:
                display_name = get_display_name(item['ts_code'], item.get('name'))
                watch_options[f"{display_name} ({item['ts_code']})"] = item['ts_code']

            selected_watch = st.selectbox(
                "选择自选股",
                options=["-- 请选择 --"] + list(watch_options.keys()),
                key="fr_watchlist_select",
                label_visibility="collapsed"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("分析", key="fr_load_watch", type="primary", use_container_width=True):
                    if selected_watch != "-- 请选择 --":
                        st.session_state.fr_stock_code = watch_options[selected_watch]
                        st.session_state.fr_data = None
                        st.session_state.fr_trigger = True
                        st.rerun()
            with col2:
                if st.button("清空", key="fr_clear_watch", use_container_width=True):
                    st.session_state.fr_stock_code = "000001.SZ"
                    st.session_state.fr_data = None
                    st.session_state.fr_trigger = False
                    st.rerun()

            st.divider()
        else:
            st.caption("暂无自选股")
            st.divider()

        # 股票代码输入
        st.markdown("**或输入股票代码:**")
        input_code = st.text_input(
            "股票代码",
            value=st.session_state.fr_stock_code,
            placeholder="如: 000001 或 600519",
            key="fr_code_input"
        )

        if input_code != st.session_state.fr_stock_code:
            st.session_state.fr_stock_code = input_code
            st.session_state.fr_data = None

        # 分析按钮
        analyze_btn = st.button("开始分析", type="primary", use_container_width=True)

    # 判断是否需要分析
    need_analyze = analyze_btn or st.session_state.fr_trigger

    # 主内容区域
    if need_analyze:
        st.session_state.fr_trigger = False
        show_financial_analysis(st.session_state.fr_stock_code)
    else:
        show_instructions()


def show_instructions():
    """显示使用说明"""
    st.info("""
    ### 📊 财报分析功能说明

    本功能提供股票财务报表分析，包括：

    - **财务概览** - 关键财务指标一览
    - **盈利能力分析** - ROE、毛利率、净利率趋势
    - **成长能力分析** - 营收、净利润增长率
    - **财务健康度评估** - 资产负债率、现金流分析
    - **综合评分** - 多维度财务健康打分

    **使用方法：**
    1. 从自选股选择或输入股票代码
    2. 点击"分析"或"开始分析"按钮
    3. 查看财务分析结果

    数据来源：AkShare (东方财富)
    """)


@st.cache_data(ttl=86400, show_spinner=False)  # 缓存一天
def get_stock_name(ts_code: str) -> str:
    """
    获取股票名称

    Args:
        ts_code: 股票代码 (如 000001.SZ)

    Returns:
        股票名称，如果获取失败则返回代码
    """
    code_num = ts_code.split('.')[0]

    # 尝试从自选股表获取（已有名称）
    try:
        from src.data.database import db_manager
        watchlist = db_manager.get_watchlist()
        for item in watchlist:
            if item['ts_code'] == ts_code or item['ts_code'] == code_num:
                if item.get('name'):
                    return item['name']
    except Exception:
        pass

    # 尝试从股票基本信息表获取
    try:
        from src.data.database import db_manager
        df = db_manager.get_stock_basic(ts_code)
        if df is not None and not df.empty:
            return df.iloc[0]['name']
    except Exception:
        pass

    # 尝试从 akshare 获取个股信息
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol=code_num)
        if df is not None and not df.empty:
            # 查找股票简称
            name_row = df[df['item'] == '股票简称']
            if not name_row.empty:
                return name_row.iloc[0]['value']
    except Exception:
        pass

    return code_num  # 返回纯数字代码，不带后缀


def show_financial_analysis(stock_code: str):
    """
    显示财务分析结果

    Args:
        stock_code: 股票代码
    """
    from src.core.utils import normalize_stock_code

    # 标准化代码
    code = normalize_stock_code(stock_code)
    code_num = code.split(".")[0]

    # 获取股票名称
    stock_name = get_stock_name(code)

    with st.spinner("正在获取财务数据..."):
        # 获取财务数据
        data = get_financial_data(code_num)

        if data is None:
            st.error("未获取到财务数据，请检查股票代码")
            return

        # 分析财务健康度 (使用已获取的数据)
        health = _financial_provider.analyze_financial_health(data)

    # 保存到 session
    st.session_state.fr_data = data

    # 显示股票名称和代码
    st.subheader(f"📈 {stock_name} ({code}) 财务分析")

    # 综合评分卡片
    show_score_card(health)

    st.divider()

    # 财务概览
    show_financial_overview(data)

    st.divider()

    # 盈利能力分析
    show_profitability_analysis(data, health)

    st.divider()

    # 成长能力分析
    show_growth_analysis(data)

    st.divider()

    # 财务风险分析
    show_risk_analysis(data, health)


def show_score_card(health: dict):
    """显示综合评分卡片"""
    score = health.get("综合评分", 0)

    # 评分等级颜色
    if score >= 80:
        color = "#28a745"  # 绿色
        rating = "优秀"
    elif score >= 60:
        color = "#17a2b8"  # 蓝色
        rating = "良好"
    elif score >= 40:
        color = "#ffc107"  # 黄色
        rating = "一般"
    else:
        color = "#dc3545"  # 红色
        rating = "较差"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
            <h2 style="color: {color}; margin: 0;">{score:.0f}</h2>
            <p style="color: #666; margin: 5px 0 0 0;">综合评分</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        profitability = health.get("盈利能力", {})
        st.metric("盈利能力", profitability.get("rating", "-"), f"{profitability.get('score', 0):.0f}分")

    with col3:
        growth = health.get("成长能力", {})
        st.metric("成长能力", growth.get("rating", "-"), f"{growth.get('score', 0):.0f}分")

    with col4:
        risk = health.get("财务风险", {})
        st.metric("财务风险", risk.get("rating", "-"), f"{risk.get('score', 0):.0f}分")


def show_financial_overview(data: dict):
    """显示财务概览"""
    st.subheader("📋 财务概览")

    indicators = data.get("indicators", {})
    years = data.get("years", [])

    if not years:
        st.warning("无财务数据")
        return

    # 取最近5年的数据
    recent_years = years[:5] if len(years) >= 5 else years

    # 常用指标
    if "常用指标" in indicators:
        st.markdown("**核心财务数据**")

        key_indicators = [
            ("营业总收入", "营收"),
            ("归母净利润", "净利润"),
            ("股东权益合计(净资产)", "净资产"),
            ("经营现金流量净额", "经营现金流"),
        ]

        rows = []
        for indicator, name in key_indicators:
            if indicator in indicators["常用指标"]:
                row = {"指标": name}
                for year in recent_years:
                    val = indicators["常用指标"][indicator].get(year)
                    if val is not None and pd.notna(val):
                        # 格式化数值
                        val_float = float(val)
                        if abs(val_float) >= 1e8:
                            row[year] = f"{val_float/1e8:.2f}亿"
                        elif abs(val_float) >= 1e4:
                            row[year] = f"{val_float/1e4:.2f}万"
                        else:
                            row[year] = f"{val_float:.2f}"
                    else:
                        row[year] = "-"
                rows.append(row)

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)


def show_profitability_analysis(data: dict, health: dict):
    """显示盈利能力分析"""
    st.subheader("💰 盈利能力分析")

    indicators = data.get("indicators", {})
    years = data.get("years", [])

    if "盈利能力" not in indicators:
        st.info("暂无盈利能力数据")
        return

    profit_indicators = indicators["盈利能力"]

    # 显示分析结果
    profitability = health.get("盈利能力", {})
    if profitability.get("analysis"):
        for analysis in profitability["analysis"]:
            if "优秀" in analysis or "良好" in analysis:
                st.success(analysis)
            elif "一般" in analysis:
                st.info(analysis)
            else:
                st.warning(analysis)

    # 指标趋势表
    st.markdown("**盈利指标趋势**")

    key_metrics = ["净资产收益率(ROE)", "毛利率", "销售净利率", "总资产报酬率(ROA)"]
    rows = []

    for metric in key_metrics:
        if metric in profit_indicators:
            row = {"指标": metric}
            for year in years[:5]:
                val = profit_indicators[metric].get(year)
                if val is not None and pd.notna(val):
                    row[year] = f"{float(val):.2f}%"
                else:
                    row[year] = "-"
            rows.append(row)

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


def show_growth_analysis(data: dict):
    """显示成长能力分析"""
    st.subheader("📈 成长能力分析")

    from src.data.financial_report import _financial_provider

    growth_data = _financial_provider.calculate_growth_rates(data)

    if not growth_data:
        st.info("暂无成长数据")
        return

    # 营收增长率
    if "营收增长率" in growth_data:
        st.markdown("**营收同比增长率**")
        revenue_growth = growth_data["营收增长率"]
        cols = st.columns(min(5, len(revenue_growth)))
        for i, (year, rate) in enumerate(sorted(revenue_growth.items(), reverse=True)[:5]):
            with cols[i]:
                delta_color = "normal" if rate >= 0 else "inverse"
                st.metric(year, f"{rate:.1f}%", delta_color=delta_color)

    # 净利润增长率
    if "净利润增长率" in growth_data:
        st.markdown("**净利润同比增长率**")
        profit_growth = growth_data["净利润增长率"]
        cols = st.columns(min(5, len(profit_growth)))
        for i, (year, rate) in enumerate(sorted(profit_growth.items(), reverse=True)[:5]):
            with cols[i]:
                delta_color = "normal" if rate >= 0 else "inverse"
                st.metric(year, f"{rate:.1f}%", delta_color=delta_color)


def show_risk_analysis(data: dict, health: dict):
    """显示财务风险分析"""
    st.subheader("⚠️ 财务风险分析")

    indicators = data.get("indicators", {})
    years = data.get("years", [])

    if "财务风险" not in indicators:
        st.info("暂无财务风险数据")
        return

    risk_indicators = indicators["财务风险"]

    # 显示分析结果
    risk = health.get("财务风险", {})
    if risk.get("analysis"):
        for analysis in risk["analysis"]:
            if "稳健" in analysis or "适中" in analysis:
                st.success(analysis)
            else:
                st.warning(analysis)

    # 资产负债率趋势
    if "资产负债率" in risk_indicators:
        st.markdown("**资产负债率趋势**")
        rows = []
        for year in years[:5]:
            val = risk_indicators["资产负债率"].get(year)
            if val is not None and pd.notna(val):
                rows.append({"年份": year, "资产负债率": f"{float(val):.2f}%"})

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()