# 极简 Todo — 开发手册

## 环境要求

- **Python** 3.10+
- **tkinter**（通常 Python 安装时自带）
  - macOS: 内置
  - Windows: 安装 Python 时勾选 "tcl/tk and IDLE"
  - Linux: `sudo apt install python3-tk`（Debian/Ubuntu）
- **PyInstaller**（仅构建打包时需要）

## 快速上手

```bash
# 1. 克隆仓库
git clone <repo-url>
cd 极简Todo

# 2. 直接运行
python todo_app.py

# 3. 打包（可选）
pip install pyinstaller

# macOS
pyinstaller 极简Todo.spec

# Windows
pyinstaller 极简Todo.spec
```

## 架构概览

### 技术栈

- **UI 层**: Python `tkinter`（内置 GUI 库）
- **数据层**: 本地 JSON 文件存储
- **Web 服务**: Python `http.server`（标准库）
- **打包**: PyInstaller（.app / .exe）

### 模块说明

| 模块 | 职责 |
|:---|:---|
| `Palette` | 配色常量，检测系统明暗模式 |
| `load_todos()` / `save_todos()` | JSON 数据读写 |
| `WebServer` / `TodoHTTPHandler` | 局域网 HTTP 共享 |
| `TaskRow` | 单条待办 UI 组件 |
| `WebToggle` | 底部共享开关 UI 组件 |
| `TodoApp` | 主窗口 + 事件处理 |

### 数据流

```
用户操作 → TodoApp → 更新 self.todos → save_todos() → JSON 文件
                                                    ↓
                                WebServer 读取 → 局域网共享
```

### 平台适配策略

```python
# 检测当前平台
IS_MACOS = sys.platform == "darwin"
IS_WIN   = sys.platform == "win32"

# 数据目录（各平台独立）
if IS_WIN:
    DATA_DIR = Path(os.environ["APPDATA"]) / "极简Todo"
else:
    DATA_DIR = Path.home() / ".local" / "share" / "todo_app"

# 字体选择
if IS_MACOS:    UI_FONT = ("SF Pro Display", 15)
elif IS_WIN:    UI_FONT = ("Segoe UI", 12)
else:           UI_FONT = ("Noto Sans CJK SC", 13)

# 深色模式检测
if IS_MACOS:    读取 defaults read -g AppleInterfaceStyle
elif IS_WIN:    读取注册表 AppsUseLightTheme
else:           读取 gsettings color-scheme
```

## 构建与发布

### macOS

```bash
# 一键构建 DMG
bash make_dmg.sh

# 或手动分步：
pyinstaller 极简Todo.spec     # → dist/极简Todo.app
hdiutil create -volname "极简Todo" \
  -srcfolder dist/极简Todo.app \
  -format UDZO 极简Todo.dmg
```

### Windows

```bash
# 一键构建
build.bat

# 或手动：
pyinstaller --onefile --windowed --name="极简Todo" --icon="assets\极简Todo.ico" todo_app.py
# → dist/极简Todo.exe
```

### Linux

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="极简Todo" todo_app.py
# → dist/极简Todo
```

## 开发约定

- 编码风格：4 空格缩进，PEP 8
- 注释语言：中文
- 文件编码：UTF-8
- 依赖原则：优先使用 Python 标准库，避免第三方依赖

## 常见问题

### Q: tkinter 报错 "No module named '_tkinter'"

**macOS**: 重新安装 Python：
```bash
brew install python-tk@3.13
```

**Linux (Ubuntu)**:
```bash
sudo apt install python3-tk
```

**Windows**: 重装 Python，确保勾选 "tcl/tk and IDLE"。

### Q: 打包后闪退

- 检查 `todo_app.py` 路径是否正确（相对路径）
- 检查 assets 目录是否存在且包含图标文件
- 用终端/CMD 运行 exe 查看报错输出

### Q: 局域网共享无法访问

- 确保设备在同一 WiFi 下
- 检查防火墙是否拦截 8080 端口
- Windows 可能需要允许 Python 通过防火墙
