@echo off
chcp 65001 >nul
echo ========================================
echo   股票分析软件 - 打包工具
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate

echo [1/3] 清理旧构建...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [2/3] 开始打包（这可能需要几分钟）...
pyinstaller ^
    --name "股票分析软件" ^
    --onefile ^
    --windowed ^
    --add-data "data;data" ^
    --hidden-import matplotlib ^
    --hidden-import pandas ^
    --hidden-import akshare ^
    --hidden-import customtkinter ^
    --collect-all matplotlib ^
    main.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo [3/3] 打包完成！
    echo 可执行文件位于: dist\股票分析软件.exe
) else (
    echo 打包失败，请检查错误信息
)

pause
