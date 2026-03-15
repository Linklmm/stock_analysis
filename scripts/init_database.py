#!/usr/bin/env python3
"""
数据库初始化脚本
Database Initialization Script

该脚本用于：
1. 创建数据库（如果不存在）
2. 创建所有数据表
3. 初始化交易日历数据（如果 Tushare 可用）

This script is used to:
1. Create database if not exists
2. Create all tables
3. Initialize trade calendar data if Tushare is available
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def check_mysql_connection() -> bool:
    """检查 MySQL 连接"""
    try:
        from sqlalchemy import create_engine, text
        from config.settings import DATABASE_CONFIG

        # 尝试连接到 MySQL 服务器
        url = f"mysql+pymysql://{DATABASE_CONFIG.user}:{DATABASE_CONFIG.password}@{DATABASE_CONFIG.host}:{DATABASE_CONFIG.port}?charset=utf8mb4"
        engine = create_engine(url)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        engine.dispose()
        print(f"✓ MySQL 连接成功: {DATABASE_CONFIG.host}:{DATABASE_CONFIG.port}")
        return True
    except Exception as e:
        print(f"✗ MySQL 连接失败: {e}")
        print("\n请检查以下配置:")
        print(f"  - MYSQL_HOST: {os.getenv('MYSQL_HOST', 'localhost')}")
        print(f"  - MYSQL_PORT: {os.getenv('MYSQL_PORT', '3306')}")
        print(f"  - MYSQL_USER: {os.getenv('MYSQL_USER', 'root')}")
        print(f"  - MYSQL_PASSWORD: {'*' * len(os.getenv('MYSQL_PASSWORD', ''))}")
        return False


def check_tushare_token() -> bool:
    """检查 Tushare Token"""
    token = os.getenv("TUSHARE_TOKEN")
    if token:
        print(f"✓ Tushare Token 已配置: {token[:10]}...")
        return True
    else:
        print("✗ Tushare Token 未配置")
        print("  请在 .env 文件中设置 TUSHARE_TOKEN")
        return False


def init_database():
    """初始化数据库"""
    print("\n" + "=" * 50)
    print("数据库初始化")
    print("=" * 50 + "\n")

    # 检查 MySQL 连接
    if not check_mysql_connection():
        print("\n请先确保 MySQL 服务已启动，并正确配置 .env 文件")
        return False

    # 创建数据库管理器
    from src.data.database import db_manager

    # 创建数据库
    print("\n[1/3] 创建数据库...")
    try:
        db_manager.create_database()
        print(f"✓ 数据库 '{db_manager.engine.url.database}' 已就绪")
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False

    # 创建数据表
    print("\n[2/3] 创建数据表...")
    try:
        db_manager.create_tables()
        print("✓ 数据表创建成功")
    except Exception as e:
        print(f"✗ 创建数据表失败: {e}")
        return False

    # 初始化交易日历
    print("\n[3/3] 初始化交易日历...")
    if check_tushare_token():
        try:
            init_trade_calendar()
            print("✓ 交易日历初始化成功")
        except Exception as e:
            print(f"✗ 交易日历初始化失败: {e}")
            print("  您可以稍后手动运行 init_trade_calendar() 来初始化")
    else:
        print("  跳过交易日历初始化（需要 Tushare Token）")

    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    return True


def init_trade_calendar():
    """初始化交易日历数据"""
    import tushare as ts
    import pandas as pd

    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError("TUSHARE_TOKEN 未配置")

    ts.set_token(token)
    pro = ts.pro_api()

    # 获取当前年份和前后各一年的交易日历
    current_year = datetime.now().year
    start_date = f"{current_year - 1}0101"
    end_date = f"{current_year + 1}1231"

    print(f"  正在获取 {start_date} 至 {end_date} 的交易日历...")

    # 获取上交所交易日历
    df_sse = pro.trade_cal(exchange="SSE", start_date=start_date, end_date=end_date)
    # 获取深交所交易日历
    df_szse = pro.trade_cal(exchange="SZSE", start_date=start_date, end_date=end_date)

    # 合并数据
    df_all = pd.concat([df_sse, df_szse], ignore_index=True)

    # 重命名列
    df_all = df_all.rename(columns={
        "cal_date": "cal_date",
        "is_open": "is_open",
        "pretrade_date": "pretrade_date"
    })

    from src.data.database import db_manager

    # 清空旧数据
    session = db_manager.get_session()
    try:
        session.execute("DELETE FROM trade_calendar")
        session.commit()
    finally:
        session.close()

    # 保存新数据
    count = db_manager.save_trade_calendar(df_all)
    print(f"  已保存 {count} 条交易日历记录")


def init_stock_basic():
    """初始化股票基本信息"""
    import tushare as ts
    import pandas as pd

    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError("TUSHARE_TOKEN 未配置")

    ts.set_token(token)
    pro = ts.pro_api()

    print("正在获取股票基本信息...")

    df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,area,industry,market,list_date")

    from src.data.database import db_manager
    count = db_manager.save_stock_basic(df)
    print(f"已保存 {count} 条股票基本信息")

    return count


def verify_database():
    """验证数据库"""
    from src.data.database import db_manager

    print("\n验证数据库...")

    session = db_manager.get_session()
    try:
        # 检查各表记录数
        from sqlalchemy import text

        tables = ["stock_daily", "index_daily", "stock_basic", "trade_calendar"]

        for table in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count} 条记录")
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument("--verify", action="store_true", help="验证数据库状态")
    parser.add_argument("--init-calendar", action="store_true", help="仅初始化交易日历")
    parser.add_argument("--init-basic", action="store_true", help="仅初始化股票基本信息")

    args = parser.parse_args()

    if args.verify:
        verify_database()
    elif args.init_calendar:
        init_trade_calendar()
    elif args.init_basic:
        init_stock_basic()
    else:
        init_database()