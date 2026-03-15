#!/bin/bash
# 安装脚本 - 创建 Conda 环境并安装所有依赖

# 配置
CONDA_ENV="stock_analysis"
PYTHON_VERSION="3.10"

echo "======================================"
echo "  中国股市 AI 分析系统 - 安装脚本"
echo "======================================"
echo ""

# 检查 Conda
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到 Conda"
    echo "请先安装 Anaconda 或 Miniconda:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# 初始化 Conda
eval "$(conda shell.bash hook)"

# 检查环境是否已存在
if conda env list | grep -q "^$CONDA_ENV "; then
    echo "环境 '$CONDA_ENV' 已存在"
    read -p "是否要删除并重新创建? (y/n): " recreate

    if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
        echo "正在删除旧环境..."
        conda env remove -n "$CONDA_ENV" -y
    else
        echo "将使用现有环境"
    fi
fi

# 创建环境
if ! conda env list | grep -q "^$CONDA_ENV "; then
    echo "正在创建 Conda 环境: $CONDA_ENV (Python $PYTHON_VERSION)"
    conda create -n "$CONDA_ENV" python=$PYTHON_VERSION -y
fi

# 激活环境
echo "正在激活环境..."
conda activate "$CONDA_ENV"

# 升级 pip
echo "正在升级 pip..."
pip install --upgrade pip

# 安装 TA-Lib（需要特殊处理）
echo ""
echo "正在安装 TA-Lib..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install ta-lib
    else
        echo "警告: 未找到 Homebrew，跳过 TA-Lib 系统依赖"
        echo "请手动安装: brew install ta-lib"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "提示: 如果 TA-Lib 安装失败，请运行:"
    echo "  sudo apt-get install -y build-essential wget"
    echo "  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz"
    echo "  tar -xzf ta-lib-0.4.0-src.tar.gz"
    echo "  cd ta-lib/ && ./configure --prefix=/usr && make && sudo make install"
fi

# 安装 Python 依赖
echo ""
echo "正在安装 Python 依赖..."
pip install -r requirements.txt

# 完成
echo ""
echo "======================================"
echo "  安装完成！"
echo "======================================"
echo ""
echo "使用以下命令启动:"
echo "  ./start.sh"
echo ""
echo "或手动启动:"
echo "  conda activate $CONDA_ENV"
echo "  streamlit run src/web/app.py"
echo ""