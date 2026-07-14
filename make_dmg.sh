#!/bin/bash
# ========================================================
#  极简 Todo — macOS DMG 构建脚本
#  需要：Python 3.10+、PyInstaller（pip install pyinstaller）
# ========================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  极简 Todo macOS 构建脚本"
echo "========================================"
echo ""

# 1. 检查 PyInstaller
echo "[1/3] 检查依赖..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
fi

# 2. 清理 + 构建 .app
echo "[2/3] 构建 .app 捆绑包..."
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist"
pyinstaller \
    --windowed \
    --name="极简Todo" \
    --icon="$SCRIPT_DIR/assets/极简Todo.icns" \
    --add-data="$SCRIPT_DIR/assets/极简Todo.icns:." \
    "$SCRIPT_DIR/todo_app.py"

# 3. 生成 DMG
echo "[3/3] 生成 DMG..."
mkdir -p "$SCRIPT_DIR/build/dmg_src"
cp -R "$SCRIPT_DIR/dist/极简Todo.app" "$SCRIPT_DIR/build/dmg_src/"

hdiutil create \
    -volname "极简Todo" \
    -srcfolder "$SCRIPT_DIR/build/dmg_src" \
    -ov \
    -format UDZO \
    "$SCRIPT_DIR/极简Todo.dmg"

echo ""
echo "========================================"
echo "  构建完成！"
echo "  $SCRIPT_DIR/极简Todo.dmg"
echo "========================================"
