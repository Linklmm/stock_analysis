#!/bin/bash
# 中国股市AI分析系统启动脚本
# 自动切换到指定的 Conda 环境并启动应用

# ========================================
# 配置区域 - 请修改为你自己的环境名称
# ========================================

# Conda 环境名称（请修改为你的环境名）
CONDA_ENV="stock_analysis"

# 项目目录
PROJECT_DIR="/Volumes/MyExt/workspace/Python/stock_analysis"

# ========================================
# 脚本执行
# ========================================

echo "======================================"
echo "  中国股市 AI 分析系统"
echo "======================================"
echo ""

# 进入项目目录
cd "$PROJECT_DIR" || { echo "错误: 无法进入项目目录"; exit 1; }

# 检查 Conda 是否可用
if command -v conda &> /dev/null; then
    # 初始化 Conda
    eval "$(conda shell.bash hook)"

    # 检查环境是否存在
    if conda env list | grep -q "^$CONDA_ENV "; then
        echo "正在激活 Conda 环境: $CONDA_ENV"
        conda activate "$CONDA_ENV"
    else
        echo "警告: Conda 环境 '$CONDA_ENV' 不存在"
        echo ""
        echo "可用的 Conda 环境:"
        conda env list
        echo ""
        echo "将使用当前环境继续..."
    fi
else
    echo "未检测到 Conda，将使用系统 Python"
fi

# 显示当前环境
echo "Python: $(which python)"
echo "Python 版本: $(python --version 2>&1)"
echo ""

# 使用 python app.py 启动
echo "正在启动应用..."
echo "请在浏览器中访问: http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"
echo ""

python app.py "$@"