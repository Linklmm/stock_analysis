"""
qlib 初始化脚本
qlib Initialization Script

该脚本用于初始化 qlib 并下载 A股数据。
This script initializes qlib and downloads A-share data.

使用方法 / Usage:
    python scripts/init_qlib.py [--download] [--force]
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import QLIB_DATA_DIR, PROJECT_ROOT
from src.core.utils import logger


def init_qlib(provider_uri: str = None, force: bool = False) -> bool:
    """
    初始化 qlib

    Args:
        provider_uri: 数据路径 / Data path
        force: 是否强制重新初始化 / Whether to force re-initialization

    Returns:
        是否成功 / Whether succeeded
    """
    try:
        import qlib
    except ImportError:
        logger.error("qlib 未安装，请运行: pip install pyqlib")
        return False

    provider_uri = provider_uri or str(QLIB_DATA_DIR)

    # 检查是否已经初始化
    if not force and qlib.get_data_provider() is not None:
        logger.info("qlib 已经初始化")
        return True

    try:
        qlib.init(
            provider_uri=provider_uri,
            region="cn"
        )
        logger.info(f"qlib 初始化成功，数据路径: {provider_uri}")
        return True

    except Exception as e:
        logger.error(f"qlib 初始化失败: {e}")
        return False


def download_qlib_data(
    target_dir: str = None,
    delete_old: bool = False,
    version: str = "v2"
) -> bool:
    """
    下载 qlib 内置数据

    Args:
        target_dir: 目标目录 / Target directory
        delete_old: 是否删除旧数据 / Whether to delete old data
        version: 数据版本 / Data version

    Returns:
        是否成功 / Whether succeeded
    """
    try:
        import qlib
        from qlib.data.data import update_data_from_github
    except ImportError:
        logger.error("qlib 未安装，请运行: pip install pyqlib")
        return False

    target_dir = target_dir or str(QLIB_DATA_DIR)

    logger.info(f"开始下载 qlib 数据到: {target_dir}")
    logger.info("注意：数据量较大（约 1GB），下载可能需要较长时间")

    try:
        # 使用 qlib 的数据下载功能
        # Use qlib's data download function
        update_data_from_github(
            target_dir=target_dir,
            delete_old=delete_old,
            version=version
        )

        logger.info("qlib 数据下载完成")

        # 重新初始化 qlib
        init_qlib(provider_uri=target_dir, force=True)

        return True

    except Exception as e:
        logger.error(f"qlib 数据下载失败: {e}")
        return False


def check_qlib_data() -> bool:
    """
    检查 qlib 数据是否存在

    Returns:
        数据是否存在 / Whether data exists
    """
    data_dir = QLIB_DATA_DIR

    # 检查必要的文件
    required_files = [
        "calendars/day.txt",
        "instruments/all.txt"
    ]

    for file_path in required_files:
        if not (data_dir / file_path).exists():
            logger.warning(f"缺少数据文件: {file_path}")
            return False

    logger.info("qlib 数据检查通过")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="qlib 初始化脚本")
    parser.add_argument(
        "--download",
        action="store_true",
        help="下载 qlib 内置数据"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新初始化"
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=None,
        help="数据目标目录"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查数据是否存在"
    )

    args = parser.parse_args()

    # 仅检查
    if args.check:
        exists = check_qlib_data()
        if exists:
            print("✓ qlib 数据存在")
        else:
            print("✗ qlib 数据不存在，请使用 --download 下载")
        return 0

    # 下载数据
    if args.download:
        success = download_qlib_data(
            target_dir=args.target_dir,
            delete_old=args.force
        )
        if not success:
            print("✗ qlib 数据下载失败")
            return 1
        print("✓ qlib 数据下载成功")
        return 0

    # 仅初始化
    success = init_qlib(
        provider_uri=args.target_dir,
        force=args.force
    )

    if success:
        print("✓ qlib 初始化成功")
        return 0
    else:
        print("✗ qlib 初始化失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())