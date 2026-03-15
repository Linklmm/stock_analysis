@echo off
REM 中国股市AI分析系统启动脚本 (Windows)

REM 配置
set CONDA_ENV=stock_analysis
set PROJECT_DIR=%~dp0

echo ======================================
echo   中国股市 AI 分析系统
echo ======================================
echo.

cd /d "%PROJECT_DIR%"

REM 检查并激活 Conda
if exist "%CONDA_EXE%" (
    call conda activate %CONDA_ENV% 2>nul
)

echo Python 版本:
python --version
echo.

echo 正在启动应用...
echo 请在浏览器中访问: http://localhost:8501
echo.
echo 按 Ctrl+C 停止服务
echo ======================================
echo.

python app.py %*

pause