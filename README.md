# 极简 Todo

> 极简黑白留白风格的本地待办清单，支持 **Windows / macOS / Linux**。

## 功能

- 📝 新增、勾选完成、删除待办
- 🌓 跟随系统自动切换深色/浅色模式
- 🌐 局域网 Web 共享（手机/平板浏览器访问）
- 💾 本地 JSON 文件存储，无需联网
- ⌨️ 键盘快捷键操作

## 快速开始

### 1. 直接运行（无需安装）

确保已安装 **Python 3.10+**，然后：

```bash
python todo_app.py
```

> 仅依赖 Python 标准库 + tkinter，无需 pip install。

### 2. 构建可执行文件

```bash
# macOS
pip install pyinstaller
bash make_dmg.sh

# Windows
pip install pyinstaller
build.bat
```

## 快捷键

| 快捷键 | 操作 |
|:---|:---|
| `Enter` | 添加待办 |
| `⌘ Delete` / `Ctrl Backspace` | 一键清空已完成 |
| `Esc` | 聚焦输入框 |

## 数据存储

| 平台 | 路径 |
|:---|:---|
| macOS | `~/.local/share/todo_app/todos.json` |
| Windows | `%APPDATA%\极简Todo\todos.json` |
| Linux | `~/.local/share/todo_app/todos.json` |

## 局域网共享

点击底部「🌐 局域网共享」开关，同一 WiFi 下的设备访问显示的地址即可查看待办。

## 项目结构

```
├── todo_app.py          # 主程序
├── 极简Todo.spec         # PyInstaller 构建配置
├── make_dmg.sh          # macOS DMG 构建脚本
├── build.bat            # Windows 构建脚本
├── assets/              # 图标资源
│   ├── 极简Todo.icns    # macOS 图标
│   └── 极简Todo.ico     # Windows 图标
└── README.md
```

## 开发

详见 [DEVELOPMENT.md](./DEVELOPMENT.md)。

## License

MIT
