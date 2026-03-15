"""
数据下载脚本
Data Download Script

该脚本用于从各种数据源下载股票数据。
This script downloads stock data from various data sources.

使用方法 / Usage:
    python scripts/download_data.py --source qlib --stocks 000001.SZ,600000.SH
    python scripts/download_data.py --source tushare --start 2020-01-01 --end 2024-12-31
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import CACHE_DIR, DATA_DIR, QLIB_DATA_DIR
from src.core.utils import logger, parse_date, normalize_stock_code
from src.data.cache import df_cache


def download_from_qlib(
    stocks: List[str],
    start_date: str,
    end_date: str,
    output_dir: str = None
) -> bool:
    """
    从 qlib 下载数据

    Args:
        stocks: 股票代码列表 / Stock code list
        start_date: 开始日期 / Start date
        end_date: 结束日期 / End date
        output_dir: 输出目录 / Output directory

    Returns:
        是否成功 / Whether succeeded
    """
    try:
        from src.data.providers.qlib_provider import QlibDataProvider

        provider = QlibDataProvider()
        if not provider.initialize():
            logger.error("qlib 初始化失败")
            return False

        output_dir = Path(output_dir or DATA_DIR / "downloaded")
        output_dir.mkdir(parents=True, exist_ok=True)

        for stock in stocks:
            try:
                logger.info(f"下载 {stock} 数据...")

                data = provider.get_market_data(
                    code=stock,
                    start_date=start_date,
                    end_date=end_date
                )

                if data.empty:
                    logger.warning(f"股票 {stock} 无数据")
                    continue

                # 保存数据
                output_file = output_dir / f"{stock.replace('.', '_')}.parquet"
                data.to_parquet(output_file)
                logger.info(f"保存到: {output_file}")

            except Exception as e:
                logger.error(f"下载 {stock} 失败: {e}")

        return True

    except Exception as e:
        logger.error(f"qlib 下载失败: {e}")
        return False


def download_from_tushare(
    stocks: List[str],
    start_date: str,
    end_date: str,
    token: str = None,
    output_dir: str = None
) -> bool:
    """
    从 Tushare 下载数据

    Args:
        stocks: 股票代码列表 / Stock code list
        start_date: 开始日期 / Start date
        end_date: 结束日期 / End date
        token: Tushare token / Tushare token
        output_dir: 输出目录 / Output directory

    Returns:
        是否成功 / Whether succeeded
    """
    try:
        import tushare as ts

        token = token or ts.get_token()
        if not token:
            logger.error("未设置 Tushare token，请设置环境变量 TUSHARE_TOKEN 或传入 token 参数")
            return False

        ts.set_token(token)
        pro = ts.pro_api()

        output_dir = Path(output_dir or DATA_DIR / "downloaded")
        output_dir.mkdir(parents=True, exist_ok=True)

        for stock in stocks:
            try:
                logger.info(f"从 Tushare 下载 {stock} 数据...")

                # 转换股票代码格式
                ts_code = normalize_stock_code(stock).replace("SH", ".SH").replace("SZ", ".SZ")

                df = pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", "")
                )

                if df.empty:
                    logger.warning(f"股票 {stock} 无数据")
                    continue

                # 转换列名
                df = df.rename(columns={
                    "trade_date": "datetime",
                    "vol": "volume"
                })
                df["datetime"] = pd.to_datetime(df["datetime"])
                df = df.set_index("datetime").sort_index()

                # 保存数据
                output_file = output_dir / f"{stock.replace('.', '_')}_tushare.parquet"
                df.to_parquet(output_file)
                logger.info(f"保存到: {output_file}")

            except Exception as e:
                logger.error(f"下载 {stock} 失败: {e}")

        return True

    except ImportError:
        logger.error("Tushare 未安装，请运行: pip install tushare")
        return False
    except Exception as e:
        logger.error(f"Tushare 下载失败: {e}")
        return False


def download_from_akshare(
    stocks: List[str],
    start_date: str,
    end_date: str,
    output_dir: str = None
) -> bool:
    """
    从 AkShare 下载数据

    Args:
        stocks: 股票代码列表 / Stock code list
        start_date: 开始日期 / Start date
        end_date: 结束日期 / End date
        output_dir: 输出目录 / Output directory

    Returns:
        是否成功 / Whether succeeded
    """
    try:
        import akshare as ak

        output_dir = Path(output_dir or DATA_DIR / "downloaded")
        output_dir.mkdir(parents=True, exist_ok=True)

        for stock in stocks:
            try:
                logger.info(f"从 AkShare 下载 {stock} 数据...")

                # 转换股票代码格式
                code = stock.split(".")[0]

                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="qfq"  # 前复权
                )

                if df.empty:
                    logger.warning(f"股票 {stock} 无数据")
                    continue

                # 转换列名
                column_mapping = {
                    "日期": "datetime",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "pct_change",
                    "涨跌额": "change",
                    "换手率": "turnover"
                }
                df = df.rename(columns=column_mapping)
                df["datetime"] = pd.to_datetime(df["datetime"])
                df = df.set_index("datetime").sort_index()

                # 保存数据
                output_file = output_dir / f"{stock.replace('.', '_')}_akshare.parquet"
                df.to_parquet(output_file)
                logger.info(f"保存到: {output_file}")

            except Exception as e:
                logger.error(f"下载 {stock} 失败: {e}")

        return True

    except ImportError:
        logger.error("AkShare 未安装，请运行: pip install akshare")
        return False
    except Exception as e:
        logger.error(f"AkShare 下载失败: {e}")
        return False


def download_stock_list(output_file: str = None) -> bool:
    """
    下载股票列表

    Args:
        output_file: 输出文件路径 / Output file path

    Returns:
        是否成功 / Whether succeeded
    """
    try:
        import akshare as ak

        logger.info("下载股票列表...")

        # A股股票列表
        stock_list = ak.stock_zh_a_spot_em()

        # 保存
        output_file = Path(output_file or DATA_DIR / "stock_list.parquet")
        stock_list.to_parquet(output_file)
        logger.info(f"股票列表已保存到: {output_file}")

        return True

    except Exception as e:
        logger.error(f"下载股票列表失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据下载脚本")

    parser.add_argument(
        "--source",
        type=str,
        choices=["qlib", "tushare", "akshare"],
        default="akshare",
        help="数据源"
    )
    parser.add_argument(
        "--stocks",
        type=str,
        default=None,
        help="股票代码，逗号分隔 (如: 000001.SZ,600000.SH)"
    )
    parser.add_argument(
        "--start",
        type=str,
        default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        help="开始日期"
    )
    parser.add_argument(
        "--end",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="结束日期"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录"
    )
    parser.add_argument(
        "--stock-list",
        action="store_true",
        help="下载股票列表"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Tushare token"
    )

    args = parser.parse_args()

    # 下载股票列表
    if args.stock_list:
        success = download_stock_list(args.output_dir)
        return 0 if success else 1

    # 解析股票代码
    if args.stocks:
        stocks = [s.strip() for s in args.stocks.split(",")]
    else:
        # 默认下载一些常见股票
        stocks = [
            "000001.SZ",  # 平安银行
            "000002.SZ",  # 万科A
            "600000.SH",  # 浦发银行
            "600036.SH",  # 招商银行
            "600519.SH",  # 贵州茅台
        ]
        logger.info(f"未指定股票，使用默认股票: {stocks}")

    # 根据数据源下载
    if args.source == "qlib":
        success = download_from_qlib(
            stocks=stocks,
            start_date=args.start,
            end_date=args.end,
            output_dir=args.output_dir
        )
    elif args.source == "tushare":
        success = download_from_tushare(
            stocks=stocks,
            start_date=args.start,
            end_date=args.end,
            token=args.token,
            output_dir=args.output_dir
        )
    else:  # akshare
        success = download_from_akshare(
            stocks=stocks,
            start_date=args.start,
            end_date=args.end,
            output_dir=args.output_dir
        )

    if success:
        print("✓ 数据下载完成")
        return 0
    else:
        print("✗ 数据下载失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())