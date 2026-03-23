@echo off
REM Windows运行脚本
REM 双击运行或从命令行: run.bat

echo SQL Excel Runner
echo =================
echo.

REM 安装依赖(首次运行)
pip install -r requirements.txt

REM 运行程序
python src\main.py %*

pause
