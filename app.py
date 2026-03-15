#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中国股市 AI 分析系统 - 主入口
Chinese Stock Market AI Analysis System - Main Entry

使用方法 / Usage:
    python app.py

    或指定端口 / Or specify port:
    python app.py --port 8502
"""

import os
import sys
import argparse
from pathlib import Path


def get_conda_env():
    """获取当前 Conda 环境名称"""
    return os.environ.get("CONDA_DEFAULT_ENV", "")


def check_dependencies():
    """检查必要依赖是否已安装"""
    required = ["streamlit", "pandas", "numpy", "plotly"]
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    return missing


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="中国股市 AI 分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
    python app.py                    # 默认启动
    python app.py --port 8502        # 指定端口
    python app.py --host 0.0.0.0     # 允许外部访问
    python app.py --no-browser       # 不自动打开浏览器
        """
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8501,
        help="服务端口号 (默认: 8501)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="服务主机地址 (默认: localhost)"
    )

    parser.add_argument(
        "--no-browser", "-n",
        action="store_true",
        help="不自动打开浏览器"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="调试模式"
    )

    args = parser.parse_args()

    # 获取项目目录
    project_dir = Path(__file__).parent.absolute()
    app_file = project_dir / "src" / "web" / "主页.py"

    # 打印启动信息
    print("=" * 50)
    print("  中国股市 AI 分析系统")
    print("  Chinese Stock Market AI Analysis System")
    print("=" * 50)
    print()

    # 显示环境信息
    conda_env = get_conda_env()
    if conda_env:
        print(f"✓ Conda 环境: {conda_env}")
    else:
        print("⚠ 未检测到 Conda 环境")

    print(f"✓ Python 版本: {sys.version.split()[0]}")
    print(f"✓ 项目目录: {project_dir}")
    print()

    # 检查依赖
    missing = check_dependencies()
    if missing:
        print(f"✗ 缺少依赖: {', '.join(missing)}")
        print()
        print("请先安装依赖:")
        print("  pip install -r requirements.txt")
        print()
        sys.exit(1)

    print("✓ 所有依赖已安装")
    print()

    # 使用 os.execvp 替换当前进程，避免 V8 fork 冲突
    streamlit_args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_file),
        "--server.port", str(args.port),
        "--server.headless", "true" if args.no_browser else "false",
    ]

    if args.host != "localhost":
        streamlit_args.extend(["--server.address", args.host])

    # 启动信息
    print(f"正在启动 Web 服务...")
    print(f"访问地址: http://{args.host}:{args.port}")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    print()

    # 使用 os.execvp 替换当前进程
    try:
        os.execvp(sys.executable, streamlit_args)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()