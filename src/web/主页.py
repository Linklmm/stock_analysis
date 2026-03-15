"""
Streamlit 主应用
Streamlit Main Application

这是中国股市 AI 分析系统的主入口，
使用 Streamlit 构建交互式 Web 界面。

This is the main entry point for the Chinese Stock Market AI Analysis System,
using Streamlit to build an interactive web interface.
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from streamlit_option_menu import option_menu

from config.settings import WEB_CONFIG
from src.core.utils import logger


def setup_page_config():
    """
    配置 Streamlit 页面
    Configure Streamlit page
    """
    st.set_page_config(
        page_title="市场概览",
        page_icon=WEB_CONFIG["page_icon"],
        layout=WEB_CONFIG["layout"],
        initial_sidebar_state=WEB_CONFIG["initial_sidebar_state"],
        menu_items={
            "About": """
            ## 中国股市 AI 分析系统

            基于 qlib 的量化分析平台，提供：
            - 趋势预测
            - 技术分析
            - 因子分析
            - 策略回测
            - 组合优化
            - 模拟交易
            """
        }
    )


def apply_custom_style():
    """
    应用自定义样式
    Apply custom styles
    """
    st.markdown(
        """
        <style>
        /* 主标题样式 */
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            padding: 1rem 0;
        }

        /* 子标题样式 */
        .sub-header {
            font-size: 1.5rem;
            font-weight: bold;
            color: #333;
            padding: 0.5rem 0;
        }

        /* 卡片样式 */
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 指标值样式 */
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1f77b4;
        }

        .metric-value.positive {
            color: #28a745;
        }

        .metric-value.negative {
            color: #dc3545;
        }

        /* 隐藏 Streamlit 默认元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* 侧边栏样式 */
        .css-1d391kg {
            background-color: #f8f9fa;
        }

        /* 数据框样式 */
        .dataframe {
            font-size: 0.9rem;
        }

        /* 图表容器 */
        .chart-container {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def init_session_state():
    """
    初始化会话状态
    Initialize session state
    """
    # 默认股票代码
    if "selected_stock" not in st.session_state:
        st.session_state.selected_stock = "000001.SZ"

    # 数据日期范围
    if "start_date" not in st.session_state:
        from datetime import datetime, timedelta
        st.session_state.start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    if "end_date" not in st.session_state:
        from datetime import datetime
        st.session_state.end_date = datetime.now().strftime("%Y-%m-%d")

    # 缓存的数据
    if "stock_data" not in st.session_state:
        st.session_state.stock_data = None

    # 模拟交易账户
    if "paper_account" not in st.session_state:
        st.session_state.paper_account = None

    # 自选股缓存
    if "watchlist_cache" not in st.session_state:
        st.session_state.watchlist_cache = None

    # 自选股刷新标志
    if "watchlist_refresh" not in st.session_state:
        st.session_state.watchlist_refresh = False

    # 自动分析标志（用于自选股快速加载）
    if "auto_analyze" not in st.session_state:
        st.session_state.auto_analyze = False


def get_stock_name(code: str) -> str:
    """
    根据股票代码获取股票中文名称
    Get Chinese stock name by code

    Args:
        code: 股票代码 (如 000001.SZ)

    Returns:
        股票中文名称
    """
    from src.data.realtime import get_realtime_stock_data

    try:
        # 尝试从实时数据获取名称
        rt_data = get_realtime_stock_data(code)
        if rt_data and rt_data.get('name'):
            name = rt_data['name']
            # 过滤掉异常名称（代码格式）
            if name and name != code and '.' not in name and len(name) > 0:
                return name
    except Exception:
        pass

    # 返回代码作为默认名称
    return code


def get_display_name(ts_code: str, name: str) -> str:
    """
    获取用于显示的股票名称（优先中文）

    Args:
        ts_code: 股票代码
        name: 数据库中存储的名称

    Returns:
        用于显示的名称
    """
    # 如果名称是有效的中文名称（不是代码格式）
    if name and '.' not in name and name != ts_code:
        return name

    # 尝试从缓存或 API 获取中文名称
    try:
        from src.data.realtime import get_realtime_stock_data
        rt_data = get_realtime_stock_data(ts_code)
        if rt_data and rt_data.get('name'):
            new_name = rt_data['name']
            if new_name and '.' not in new_name and new_name != ts_code:
                # 更新数据库中的名称
                try:
                    from src.data.database import db_manager
                    db_manager.update_watchlist_name(ts_code, new_name)
                except Exception:
                    pass
                return new_name
    except Exception:
        pass

    # 返回代码
    return ts_code


def create_sidebar():
    """
    创建侧边栏
    Create sidebar
    """
    with st.sidebar:
        # Logo 和标题
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0;">
                <h1 style="color: #1f77b4;">📈 股市分析</h1>
                <p style="color: #666;">AI 驱动的量化分析平台</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        # 导航菜单
        selected = option_menu(
            menu_title=None,
            options=[
                "📊 市场概览",
                "🔮 趋势预测",
                "📈 技术分析",
                "📑 财报分析",
                "🔬 因子分析",
                "⏱️ 策略回测",
                "💼 组合管理",
                "💹 模拟交易",
                "⚙️ 系统设置"
            ],
            icons=None,
            menu_icon=None,
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "#f8f9fa"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "5px",
                    "padding": "10px",
                    "border-radius": "5px"
                },
                "nav-link-selected": {
                    "background-color": "#1f77b4",
                    "color": "white"
                }
            }
        )

        st.divider()

        # 快速股票选择
        st.subheader("快速选择")
        stock_input = st.text_input(
            "股票代码",
            value=st.session_state.selected_stock,
            placeholder="如: 000001.SZ",
            help="输入股票代码，支持格式: 000001, 000001.SZ"
        )

        if stock_input != st.session_state.selected_stock:
            st.session_state.selected_stock = stock_input
            st.rerun()

        # 日期范围选择
        st.subheader("日期范围")
        col1, col2 = st.columns(2)
        with col1:
            # 将字符串转换为 date 对象
            from datetime import datetime
            try:
                default_start = datetime.strptime(st.session_state.start_date, "%Y-%m-%d").date()
            except:
                from datetime import timedelta
                default_start = (datetime.now() - timedelta(days=365)).date()

            start_date = st.date_input(
                "开始日期",
                value=default_start,
                key="start_date_input"
            )
        with col2:
            try:
                default_end = datetime.strptime(st.session_state.end_date, "%Y-%m-%d").date()
            except:
                default_end = datetime.now().date()

            end_date = st.date_input(
                "结束日期",
                value=default_end,
                key="end_date_input"
            )

        # 更新会话状态
        if str(start_date) != st.session_state.start_date:
            st.session_state.start_date = str(start_date)
        if str(end_date) != st.session_state.end_date:
            st.session_state.end_date = str(end_date)

        st.divider()

        # 自选股管理
        st.subheader("⭐ 自选股")

        # 获取自选股列表
        try:
            from src.data.database import db_manager
            if st.session_state.watchlist_refresh or st.session_state.watchlist_cache is None:
                st.session_state.watchlist_cache = db_manager.get_watchlist()
                st.session_state.watchlist_refresh = False
            watchlist = st.session_state.watchlist_cache
        except Exception:
            watchlist = []

        # 显示自选股列表
        if watchlist:
            for item in watchlist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    # 获取显示名称（优先中文）
                    display_name = get_display_name(item['ts_code'], item.get('name'))
                    # 点击选择股票
                    if st.button(
                        display_name,
                        key=f"watch_{item['ts_code']}",
                        help=f"代码: {item['ts_code']}"
                    ):
                        st.session_state.selected_stock = item['ts_code']
                        st.session_state.auto_analyze = True
                        st.rerun()
                with col2:
                    # 删除按钮
                    if st.button("🗑️", key=f"del_{item['ts_code']}", help="移除"):
                        try:
                            db_manager.remove_from_watchlist(item['ts_code'])
                            st.session_state.watchlist_refresh = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"移除失败: {e}")
        else:
            st.caption("暂无自选股")

        # 添加自选股
        with st.expander("➕ 添加自选股"):
            new_code = st.text_input(
                "股票代码",
                placeholder="如: 000001 或 600519",
                key="new_watch_code"
            )
            if st.button("添加", key="add_watch_btn"):
                if new_code:
                    try:
                        from src.core.utils import normalize_stock_code
                        code = normalize_stock_code(new_code)
                        # 自动获取股票名称
                        with st.spinner("获取股票信息..."):
                            name = get_stock_name(code)
                        if db_manager.add_to_watchlist(code, name):
                            st.session_state.watchlist_refresh = True
                            st.success(f"✅ 已添加: {name} ({code})")
                            st.rerun()
                        else:
                            st.warning(f"股票 {code} 已在自选股中")
                    except Exception as e:
                        st.error(f"添加失败: {e}")
                else:
                    st.warning("请输入股票代码")

        st.divider()

        # 系统状态
        st.caption(f"版本: 1.0.0")
        st.caption(f"数据源: AkShare")

        return selected


def main():
    """
    主函数
    Main function
    """
    # 配置页面
    setup_page_config()

    # 应用自定义样式
    apply_custom_style()

    # 初始化会话状态
    init_session_state()

    # 创建侧边栏并获取选择
    selected_page = create_sidebar()

    # 根据选择显示不同页面
    pages = {
        "📊 市场概览": "pages/1_market_overview.py",
        "🔮 趋势预测": "pages/2_prediction.py",
        "📈 技术分析": "pages/3_技术分析.py",
        "📑 财报分析": "pages/4_财报分析.py",
        "🔬 因子分析": "pages/5_factors.py",
        "⏱️ 策略回测": "pages/6_backtest.py",
        "💼 组合管理": "pages/7_portfolio.py",
        "💹 模拟交易": "pages/8_paper_trading.py",
        "⚙️ 系统设置": "pages/9_settings.py"
    }

    # 显示主内容区域
    try:
        # 市场概览页面直接加载，其他页面使用 st.switch_page
        if selected_page == "📊 市场概览":
            # 直接在这里显示市场概览内容
            show_market_overview()
        else:
            page_file = pages.get(selected_page)
            if page_file:
                # 尝试加载页面
                page_path = Path(__file__).parent / page_file
                if page_path.exists():
                    st.switch_page(page_file)
                else:
                    st.info(f"🚧 {selected_page} 页面开发中...")
            else:
                st.info("🚧 该功能开发中...")

    except Exception as e:
        st.error(f"页面加载错误: {e}")
        logger.error(f"页面加载错误: {e}")


def show_market_overview():
    """
    显示市场概览页面
    Show market overview page
    """
    from datetime import datetime, timedelta
    from src.data.realtime import get_realtime_index_data

    # 页面标题
    st.markdown(
        '<p class="main-header">📊 市场概览</p>',
        unsafe_allow_html=True
    )

    # 获取实时指数数据
    index_data = get_realtime_index_data()

    # 市场指数概览
    st.subheader("市场指数")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sh_data = index_data.get("上证指数", {})
        st.metric(
            label="上证指数",
            value=f"{sh_data.get('value', 0):,.2f}",
            delta=f"{sh_data.get('change_pct', 0):+.2f}%",
            delta_color="normal" if sh_data.get('change_pct', 0) >= 0 else "inverse"
        )

    with col2:
        sz_data = index_data.get("深证成指", {})
        st.metric(
            label="深证成指",
            value=f"{sz_data.get('value', 0):,.2f}",
            delta=f"{sz_data.get('change_pct', 0):+.2f}%",
            delta_color="normal" if sz_data.get('change_pct', 0) >= 0 else "inverse"
        )

    with col3:
        cy_data = index_data.get("创业板指", {})
        st.metric(
            label="创业板指",
            value=f"{cy_data.get('value', 0):,.2f}",
            delta=f"{cy_data.get('change_pct', 0):+.2f}%",
            delta_color="normal" if cy_data.get('change_pct', 0) >= 0 else "inverse"
        )

    with col4:
        kc_data = index_data.get("科创50", {})
        st.metric(
            label="科创50",
            value=f"{kc_data.get('value', 0):,.2f}",
            delta=f"{kc_data.get('change_pct', 0):+.2f}%",
            delta_color="normal" if kc_data.get('change_pct', 0) >= 0 else "inverse"
        )

    st.divider()

    # 快速分析区域 - 放在前面，这是最重要的功能
    st.subheader("📈 股票快速分析")

    from src.data.database import db_manager
    from src.core.utils import normalize_stock_code

    # 股票选择行
    col1, col2 = st.columns([4, 1])

    with col1:
        stock_code = st.text_input(
            "输入股票代码",
            value=st.session_state.selected_stock,
            placeholder="如: 000001 或 600519",
            label_visibility="collapsed"
        )

    with col2:
        analyze_btn = st.button("🔍 分析", type="primary", use_container_width=True)

    # 显示股票分析结果
    # 条件：点击分析按钮、有缓存数据、或自动分析标志
    if analyze_btn or st.session_state.stock_data is not None or st.session_state.auto_analyze:
        # auto_analyze 模式优先使用数据库缓存
        use_cache = st.session_state.auto_analyze
        show_stock_analysis(stock_code, use_cache=use_cache)
        # 重置自动分析标志
        st.session_state.auto_analyze = False

    st.divider()

    # 自选股快速选择区域
    try:
        watchlist = db_manager.get_watchlist()
    except Exception:
        watchlist = []

    if watchlist:
        st.subheader("⭐ 我的自选股")

        # 使用 selectbox 或按钮选择（显示中文名称）
        watch_options = {}
        for item in watchlist:
            display_name = get_display_name(item['ts_code'], item.get('name'))
            watch_options[f"{display_name} ({item['ts_code']})"] = item['ts_code']

        st.markdown("**选择自选股进行分析:**")
        col1, col2 = st.columns([5, 1])
        with col1:
            selected_watch = st.selectbox(
                "选择自选股",
                options=list(watch_options.keys()),
                key="watchlist_select",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("加载", use_container_width=True, key="load_watch"):
                if selected_watch:
                    st.session_state.selected_stock = watch_options[selected_watch]
                    st.session_state.auto_analyze = True
                    st.rerun()

        # 显示自选股列表（简洁版）
        st.markdown("**自选股列表:**")
        cols_per_row = 5
        cols = st.columns(cols_per_row)
        for idx, item in enumerate(watchlist):
            col = cols[idx % cols_per_row]
            with col:
                # 获取显示名称，取前4个字符
                display_name = get_display_name(item['ts_code'], item.get('name'))
                btn_label = display_name[:4] if display_name and display_name != item['ts_code'] else item['ts_code'][:6]
                if st.button(btn_label, key=f"watch_btn_{item['ts_code']}", use_container_width=True):
                    st.session_state.selected_stock = item['ts_code']
                    st.session_state.auto_analyze = True
                    st.rerun()

        st.divider()

    # 市场资讯
    st.subheader("📰 市场资讯")

    tab1, tab2, tab3 = st.tabs(["财经新闻", "涨停板", "最新公告"])

    with tab1:
        show_financial_news()

    with tab2:
        show_limit_up_stocks()

    with tab3:
        show_stock_announcements()


def show_stock_analysis(stock_code: str, use_cache: bool = False):
    """
    显示股票分析结果
    Show stock analysis results

    Args:
        stock_code: 股票代码
        use_cache: 是否优先使用缓存数据（True时只从数据库读取，不调用API）
    """
    from src.core.utils import normalize_stock_code
    from src.data.realtime import get_realtime_stock_data, get_stock_history
    from src.data.database import db_manager

    try:
        # 标准化股票代码
        code = normalize_stock_code(stock_code)

        # 转换为 TS 代码格式
        code_num = code.split(".")[0]
        if code.startswith("6"):
            ts_code = f"{code_num}.SH"
        else:
            ts_code = f"{code_num}.SZ"

        realtime_data = None
        hist_data = None

        # 显示加载状态
        with st.spinner("正在加载数据..."):
            if use_cache:
                # 缓存模式：只从数据库读取
                from datetime import datetime, timedelta

                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

                # 从数据库获取历史数据
                hist_data = db_manager.get_stock_daily(ts_code, start_date, end_date)

                if hist_data is not None and not hist_data.empty:
                    # 从历史数据构造实时数据
                    latest = hist_data.iloc[-1]
                    prev = hist_data.iloc[-2] if len(hist_data) > 1 else latest
                    close = float(latest.get("close", 0))
                    pre_close = float(prev.get("close", 0))
                    change_pct = round((close - pre_close) / pre_close * 100, 2) if pre_close > 0 else 0

                    realtime_data = {
                        "code": code,
                        "name": code,
                        "price": close,
                        "open": float(latest.get("open", 0)),
                        "high": float(latest.get("high", 0)),
                        "low": float(latest.get("low", 0)),
                        "volume": float(latest.get("vol", 0) or latest.get("volume", 0)),
                        "amount": float(latest.get("amount", 0)),
                        "change_pct": change_pct,
                        "turnover": 0,
                    }
                    st.session_state.stock_data = hist_data
                else:
                    st.warning("数据库中无缓存数据，请点击「分析」按钮获取数据")
                    return
            else:
                # 正常模式：从API获取数据（会自动缓存到数据库）
                realtime_data = get_realtime_stock_data(code)
                hist_data = get_stock_history(
                    code=code,
                    start_date=str(st.session_state.start_date_input),
                    end_date=str(st.session_state.end_date_input)
                )

                if realtime_data is None and (hist_data is None or hist_data.empty):
                    st.warning("未获取到数据，请检查股票代码")
                    return

                # 保存历史数据到 session
                if hist_data is not None and not hist_data.empty:
                    st.session_state.stock_data = hist_data

        # 股票标题行和自选股操作
        is_in_watchlist = db_manager.is_in_watchlist(code)

        # 获取股票名称用于显示
        stock_name = code
        if realtime_data and realtime_data.get('name'):
            stock_name = realtime_data['name']

        # 标题行
        st.subheader(f"📈 {stock_name}")

        # 自选股操作按钮（只显示一个）
        if is_in_watchlist:
            if st.button("🗑️ 移出自选股", key=f"remove_watch_{code}", use_container_width=True):
                if db_manager.remove_from_watchlist(code):
                    st.session_state.watchlist_refresh = True
                    st.success(f"已将 {stock_name} 移出自选股")
                    st.rerun()
        else:
            if st.button("⭐ 加入自选股", key=f"add_to_watch_{code}", type="primary", use_container_width=True):
                if db_manager.add_to_watchlist(code, stock_name):
                    st.session_state.watchlist_refresh = True
                    st.success(f"✅ 已将 {stock_name} 加入自选股")
                    st.rerun()

        st.markdown("---")

        # 显示实时数据
        if realtime_data:
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                change_pct = realtime_data.get("change_pct", 0)
                st.metric(
                    "最新价",
                    f"¥{realtime_data.get('price', 0):.2f}",
                    f"{change_pct:+.2f}%",
                    delta_color="normal" if change_pct >= 0 else "inverse"
                )

            with col2:
                st.metric("最高价", f"¥{realtime_data.get('high', 0):.2f}")

            with col3:
                st.metric("最低价", f"¥{realtime_data.get('low', 0):.2f}")

            with col4:
                vol = realtime_data.get('volume', 0)
                st.metric("成交量", f"{vol/1e4:.0f}万" if vol else "-")

            with col5:
                st.metric("换手率", f"{realtime_data.get('turnover', 0):.2f}%")

        # 显示历史价格走势图
        if hist_data is not None and not hist_data.empty:
            st.subheader("历史走势")

            # 统一列名（MySQL缓存用vol，API用volume）
            if 'vol' in hist_data.columns and 'volume' not in hist_data.columns:
                hist_data['volume'] = hist_data['vol']

            from src.web.components.charts import create_line_chart

            fig = create_line_chart(hist_data, title=f"{code} 价格走势")
            st.plotly_chart(fig, use_container_width=True)

            # 数据表格
            with st.expander("查看详细数据"):
                display_cols = ["open", "high", "low", "close"]
                if "volume" in hist_data.columns:
                    display_cols.append("volume")
                elif "vol" in hist_data.columns:
                    display_cols.append("vol")

                display_data = hist_data[display_cols].tail(20).copy()

                # 重命名为中文表头
                rename_map = {
                    "open": "开盘价",
                    "high": "最高价",
                    "low": "最低价",
                    "close": "收盘价",
                    "volume": "成交量",
                    "vol": "成交量"
                }
                display_data = display_data.rename(columns=rename_map)

                # 格式化
                format_dict = {
                    "开盘价": "{:.2f}",
                    "最高价": "{:.2f}",
                    "最低价": "{:.2f}",
                    "收盘价": "{:.2f}",
                    "成交量": "{:,.0f}"
                }

                st.dataframe(
                    display_data.style.format(format_dict),
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"分析失败: {e}")
        logger.error(f"股票分析失败: {e}")


def show_financial_news():
    """
    显示财经新闻
    Display financial news
    """
    from src.data.market_news import get_financial_news

    # 刷新按钮
    col1, col2 = st.columns([6, 1])
    with col2:
        refresh = st.button("🔄 刷新", key="refresh_news", use_container_width=True)

    with st.spinner("正在加载新闻..."):
        news_list = get_financial_news(count=15)

    if not news_list:
        st.info("暂无新闻数据")
        return

    # 显示新闻列表
    for i, news in enumerate(news_list):
        with st.container():
            # 新闻标题（可点击跳转）
            title = news.get("title", "")
            url = news.get("url", "")
            source = news.get("source", "")
            publish_time = news.get("publish_time", "")

            if url:
                st.markdown(f"**[{title}]({url})**")
            else:
                st.markdown(f"**{title}**")

            # 元信息
            meta = []
            if source:
                meta.append(f"📰 {source}")
            if publish_time:
                meta.append(f"🕐 {publish_time}")

            if meta:
                st.caption(" | ".join(meta))

            # 使用 expander 显示详细内容
            content = news.get("content", "")
            if content:
                with st.expander("查看详情"):
                    st.write(content)
                    if url:
                        st.markdown(f"[查看原文]({url})")

            st.divider()


def show_limit_up_stocks():
    """
    显示涨停股票池
    Display limit-up stocks pool
    """
    from src.data.market_news import get_limit_up_stocks

    # 刷新按钮
    col1, col2 = st.columns([6, 1])
    with col2:
        refresh = st.button("🔄 刷新", key="refresh_limit_up", use_container_width=True)

    with st.spinner("正在加载涨停数据..."):
        data = get_limit_up_stocks()

    stocks = data.get("stocks", [])
    total = data.get("total", 0)
    continuous_count = data.get("continuous_count", 0)

    if not stocks:
        st.info("今日暂无涨停股票")
        return

    # 涨停统计
    st.markdown(f"**📊 今日涨停统计**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("涨停家数", f"{total} 家")
    with col2:
        st.metric("连板股数量", f"{continuous_count} 只")

    st.divider()

    # 涨停股票列表
    st.markdown("**📋 涨停股票列表**")

    # 转换为 DataFrame 显示
    import pandas as pd
    df_data = []
    for stock in stocks:
        df_data.append({
            "代码": stock.get("code", ""),
            "名称": stock.get("name", ""),
            "涨幅": f"+{stock.get('pct_chg', 0):.2f}%",
            "连板": f"{stock.get('continuous', 1)}板" if stock.get("continuous", 1) > 1 else "首板",
            "行业": stock.get("industry", "-"),
            "涨停原因": stock.get("reason", "-"),
        })

    df = pd.DataFrame(df_data)

    # 使用 data_editor 支持点击跳转
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "代码": st.column_config.TextColumn("代码", width="small"),
            "名称": st.column_config.TextColumn("名称", width="small"),
            "涨幅": st.column_config.TextColumn("涨幅", width="small"),
            "连板": st.column_config.TextColumn("连板", width="small"),
            "行业": st.column_config.TextColumn("行业", width="medium"),
            "涨停原因": st.column_config.TextColumn("涨停原因", width="large"),
        }
    )

    # 点击跳转提示
    st.caption("💡 点击股票代码可在上方输入框中输入进行分析")


def show_stock_announcements():
    """
    显示股票公告
    Display stock announcements
    """
    from src.data.market_news import get_stock_announcements

    # 筛选类型
    announcement_types = ["全部", "回购预案", "业绩预告", "重大事项", "股权变动", "高管变动"]

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_type = st.selectbox(
            "公告类型",
            options=announcement_types,
            key="announcement_type_filter",
            label_visibility="collapsed"
        )
    with col2:
        refresh = st.button("🔄 刷新", key="refresh_announcements", use_container_width=True)

    with st.spinner("正在加载公告..."):
        announcements = get_stock_announcements(
            count=50,
            announcement_type=selected_type if selected_type != "全部" else None
        )

    if not announcements:
        st.info("暂无公告数据")
        return

    # 显示公告列表
    import pandas as pd
    df_data = []
    for ann in announcements:
        df_data.append({
            "代码": ann.get("code", ""),
            "名称": ann.get("name", ""),
            "公告标题": ann.get("title", ""),
            "类型": ann.get("type", ""),
            "日期": str(ann.get("date", "")),
            "链接": ann.get("url", ""),
        })

    df = pd.DataFrame(df_data)

    # 使用 data_editor 显示
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "代码": st.column_config.TextColumn("代码", width="small"),
            "名称": st.column_config.TextColumn("名称", width="small"),
            "公告标题": st.column_config.LinkColumn(
                "公告标题",
                width="large",
                display_text="公告标题"
            ),
            "类型": st.column_config.TextColumn("类型", width="medium"),
            "日期": st.column_config.TextColumn("日期", width="small"),
            "链接": st.column_config.TextColumn("链接", width="small"),
        }
    )

    st.caption(f"📊 共 {len(announcements)} 条公告")


if __name__ == "__main__":
    main()