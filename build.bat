@echo off
chcp 65001 >nul
:: ========================================================
::  极简 Todo — Windows 一键构建脚本
::  需要：Python 3.10+、PyInstaller（pip install pyinstaller）
:: ========================================================

echo ========================================
echo   极简 Todo Windows 构建脚本
echo ========================================
echo.

echo [1/3] 检查依赖...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

echo [2/3] 清理旧文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [3/3] 构建 exe...
pyinstaller --onefile --windowed --name="极简Todo" --icon="assets\极简Todo.ico" todo_app.py

echo.
echo ========================================
echo   构建完成！
echo   dist\极简Todo.exe
echo ========================================
pause
