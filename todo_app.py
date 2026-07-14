#!/usr/bin/env python3
"""
极简 Todo — 跨平台本地待办清单
• 黑白高级留白 UI
• 跟随系统自动深浅色切换
• 本地 JSON 文件存储
• 新增 / 勾选完成 / 删除
• 局域网 Web 共享（HTTP 服务器 + 底部开关）

支持平台：Windows / macOS / Linux
依赖：仅 Python 3.10+ 标准库 + tkinter
"""

import json
import subprocess
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime
from typing import Optional
import threading
import socket
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── 平台检测 ──────────────────────────────────────────────
IS_MACOS  = sys.platform == "darwin"
IS_WIN    = sys.platform == "win32"

# ── 数据文件路径 ──────────────────────────────────────────
if IS_WIN:
    DATA_DIR  = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "极简Todo"
else:
    DATA_DIR  = Path.home() / ".local" / "share" / "todo_app"

DATA_FILE = DATA_DIR / "todos.json"
WEB_PORT  = 8080

# ── 跨平台字体 ────────────────────────────────────────────
if IS_MACOS:
    UI_FONT   = ("SF Pro Display", 15)
    UI_FONT_S = ("SF Pro Display", 14)
    UI_FONT_L = ("SF Pro Display", 11)
    WIN_WIDTH = 420
    WIN_HEIGHT= 640
elif IS_WIN:
    UI_FONT   = ("Segoe UI", 12)
    UI_FONT_S = ("Segoe UI", 11)
    UI_FONT_L = ("Segoe UI", 10)
    WIN_WIDTH = 420
    WIN_HEIGHT= 640
else:
    UI_FONT   = ("Noto Sans CJK SC", 13)
    UI_FONT_S = ("Noto Sans CJK SC", 12)
    UI_FONT_L = ("Noto Sans CJK SC", 10)
    WIN_WIDTH = 420
    WIN_HEIGHT= 640


# ── 配色常量 ──────────────────────────────────────────────
class Palette:
    """黑白极简调色板，跟随系统明暗切换"""
    _dark      = False
    BG         = "#ffffff"
    FG         = "#1d1d1f"
    MUTED      = "#86868b"
    DIM        = "#aeaeb2"
    LINE       = "#e5e5ea"
    ACCENT     = "#0a84ff"
    DELETE     = "#ff453a"
    HOVER_BG   = "#f2f2f7"

    @classmethod
    def _apply(cls):
        if cls._dark:
            cls.BG       = "#1c1c1e"
            cls.FG       = "#f5f5f7"
            cls.MUTED    = "#8e8e93"
            cls.DIM      = "#6e6e73"
            cls.LINE     = "#38383a"
            cls.HOVER_BG = "#2c2c2e"
        else:
            cls.BG       = "#ffffff"
            cls.FG       = "#1d1d1f"
            cls.MUTED    = "#86868b"
            cls.DIM      = "#aeaeb2"
            cls.LINE     = "#e5e5ea"
            cls.HOVER_BG = "#f2f2f7"

    @classmethod
    def detect(cls) -> bool:
        if IS_MACOS:
            cls._detect_macos()
        elif IS_WIN:
            cls._detect_windows()
        else:
            cls._detect_linux()
        cls._apply()
        return cls._dark

    @classmethod
    def _detect_macos(cls):
        try:
            r = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=3,
            )
            cls._dark = (r.stdout.strip() == "Dark")
        except Exception:
            cls._dark = False

    @classmethod
    def _detect_windows(cls):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            cls._dark = (value == 0)
        except Exception:
            cls._dark = False

    @classmethod
    def _detect_linux(cls):
        try:
            r = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=3,
            )
            cls._dark = "dark" in r.stdout.strip().lower()
        except Exception:
            cls._dark = False

    @classmethod
    def refresh(cls):
        cls.detect()


# ── 数据层 ────────────────────────────────────────────────
def load_todos() -> list[dict]:
    """加载待办列表，容错返回空列表"""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos):
    """持久化待办列表"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def get_lan_ip() -> str:
    """获取局域网 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── HTML 模板 ──────────────────────────────────────────────
WEB_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>极简 Todo</title>
<style>
  :root {{
    --bg: #ffffff;
    --fg: #1d1d1f;
    --muted: #86868b;
    --line: #e5e5ea;
    --accent: #0a84ff;
    --done-fg: #aeaeb2;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #1c1c1e;
      --fg: #f5f5f7;
      --muted: #8e8e93;
      --line: #38383a;
      --accent: #0a84ff;
      --done-fg: #6e6e73;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "SF Pro Display", "Segoe UI", "Helvetica Neue", sans-serif;
    background: var(--bg); color: var(--fg);
    max-width: 600px; margin: 0 auto; padding: 32px 28px;
    min-height: 100vh;
  }}
  h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
  .count {{ font-size: 12px; color: var(--muted); margin-bottom: 28px; }}
  .todo-list {{ list-style: none; }}
  .todo-item {{
    display: flex; align-items: center; gap: 12px;
    padding: 14px 0; border-bottom: 1px solid var(--line);
  }}
  .todo-item:last-child {{ border-bottom: none; }}
  .check {{
    width: 22px; height: 22px; border-radius: 50%;
    border: 1.5px solid var(--muted);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; color: var(--accent); flex-shrink: 0;
    cursor: default;
  }}
  .todo-done .check {{
    background: var(--accent); border-color: var(--accent); color: #fff;
  }}
  .todo-done .text {{
    color: var(--done-fg); text-decoration: line-through;
  }}
  .text {{ font-size: 15px; flex: 1; word-break: break-all; }}
  .time {{ font-size: 11px; color: var(--muted); white-space: nowrap; }}
</style>
</head>
<body>
<h1>极简 Todo</h1>
<p class="count">{done_count}/{total} 已完成</p>
<ul class="todo-list">
{todo_items}
</ul>
</body>
</html>
"""


# ── Web 服务器 ────────────────────────────────────────────
class TodoHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        todos = load_todos()
        total = len(todos)
        done_count = sum(1 for t in todos if t.get("done"))
        items = []
        for t in todos:
            done_class = "todo-done" if t.get("done") else ""
            check_mark = "✓" if t.get("done") else ""
            created = t.get("created_at", "")[:10]
            items.append(
                f'<li class="todo-item {done_class}">'
                f'<span class="check">{check_mark}</span>'
                f'<span class="text">{t.get("text", "")}</span>'
                f'<span class="time">{created}</span>'
                f'</li>'
            )
        html = WEB_HTML_TEMPLATE.format(
            done_count=done_count,
            total=total,
            todo_items="\n".join(items),
        )
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass


class WebServer:
    def __init__(self):
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._server = HTTPServer(("0.0.0.0", WEB_PORT), TodoHTTPHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self):
        if not self._running:
            return
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        self._running = False


# ── UI 组件 ────────────────────────────────────────────────
class WebToggle(tk.Frame):
    """局域网共享开关"""
    def __init__(self, parent, on_toggle=None):
        super().__init__(parent, bg=Palette.BG)
        self._on = False
        self._on_toggle = on_toggle

        self.toggle_btn = tk.Label(
            self, text="🌐 局域网共享", font=UI_FONT_L,
            bg=Palette.BG, fg=Palette.MUTED, cursor="hand2",
        )
        self.toggle_btn.pack(side="left")
        self.toggle_btn.bind("<Button-1>", self._toggle)

        self.url_label = tk.Label(
            self, text="", font=UI_FONT_L,
            bg=Palette.BG, fg=Palette.ACCENT,
        )
        self.url_label.pack(side="right")

    def _toggle(self, event=None):
        self._on = not self._on
        if self._on:
            self.toggle_btn.configure(fg=Palette.ACCENT, text="🌐 已开启")
        else:
            self.toggle_btn.configure(fg=Palette.MUTED, text="🌐 局域网共享")
        if self._on_toggle:
            self._on_toggle(self._on)


class TaskRow(tk.Frame):
    """单条待办行"""
    def __init__(self, parent, todo: dict, index: int, on_change=None):
        super().__init__(parent, bg=Palette.BG)
        self.todo = todo
        self.index = index
        self.on_change = on_change

        # 勾选框
        check_text = "✓" if todo.get("done") else ""
        self.check = tk.Label(
            self, text=check_text, font=("", 12),
            width=2, height=1,
            bg=Palette.BG, fg=Palette.ACCENT if todo.get("done") else Palette.MUTED,
            cursor="hand2",
        )
        self.check.pack(side="left", padx=(0, 10))
        self.check.bind("<Button-1>", self._toggle)

        # 文字
        fg = Palette.DIM if todo.get("done") else Palette.FG
        font_style = ("overstrike" if todo.get("done") else "normal",)
        self.label = tk.Label(
            self, text=todo.get("text", ""), font=UI_FONT,
            bg=Palette.BG, fg=fg, anchor="w", justify="left",
        )
        if todo.get("done"):
            self.label.configure(font=(UI_FONT[0], UI_FONT[1], "overstrike"))
        self.label.pack(side="left", fill="x", expand=True)

        # 删除按钮
        self.delete_btn = tk.Label(
            self, text="×", font=("", 16),
            bg=Palette.BG, fg=Palette.DELETE, cursor="hand2",
        )
        self.delete_btn.pack(side="right", padx=(10, 0))
        self.delete_btn.bind("<Button-1>", self._delete)

    def _toggle(self, event=None):
        self.todo["done"] = not self.todo.get("done", False)
        self.todo["updated_at"] = datetime.now().isoformat()
        if self.on_change:
            self.on_change()

    def _delete(self, event=None):
        if self.on_change:
            self.on_change(delete_index=self.index)


# ── 主应用 ────────────────────────────────────────────────
class TodoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("极简 Todo")
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.root.minsize(320, 480)
        self.root.configure(bg=Palette.BG)

        # 应用图标
        try:
            icon_path = Path(__file__).parent / "assets"
            if IS_WIN and (icon_path / "极简Todo.ico").exists():
                self.root.iconbitmap(str(icon_path / "极简Todo.ico"))
            # macOS uses .icns internally via PyInstaller bundle
        except Exception:
            pass

        self.web_server = WebServer()
        self.todos = load_todos()
        self.task_rows: list[TaskRow] = []

        self._build_ui()
        self._render_tasks()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 快捷键
        self.root.bind("<Return>", lambda e: self.add_todo())
        self.root.bind("<Command-BackSpace>", lambda e: self._delete_last_done())
        self.root.bind("<Control-BackSpace>", lambda e: self._delete_last_done())
        self.root.bind("<Escape>", lambda e: self._focus_input())

        self.root.mainloop()

    def _on_close(self):
        self.web_server.stop()
        self.root.destroy()

    def _build_ui(self):
        # 标题栏
        self.header = tk.Frame(self.root, bg=Palette.BG)
        self.header.pack(fill="x", padx=28, pady=(28, 6))

        self.title_label = tk.Label(
            self.header, text="极简 Todo", font=("", 20, "bold"),
            bg=Palette.BG, fg=Palette.FG,
        )
        self.title_label.pack(side="left")

        self.count_label = tk.Label(
            self.header, text="", font=UI_FONT_S,
            bg=Palette.BG, fg=Palette.MUTED,
        )
        self.count_label.pack(side="left", padx=(10, 0))

        # 输入区
        self.input_frame = tk.Frame(self.root, bg=Palette.BG)
        self.input_frame.pack(fill="x", padx=28, pady=(0, 20))

        self.entry = tk.Entry(
            self.input_frame,
            font=UI_FONT,
            bg=Palette.BG, fg=Palette.FG,
            insertbackground=Palette.ACCENT,
            relief="solid", bd=0,
            highlightthickness=0,
        )
        self.entry.pack(fill="x", ipady=10)

        self.entry_line = tk.Frame(self.input_frame, height=1, bg=Palette.LINE)
        self.entry_line.pack(fill="x")

        self.entry.focus_set()

        # 任务列表滚动区
        self.task_container = tk.Frame(self.root, bg=Palette.BG)
        self.task_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.task_container, bg=Palette.BG,
            highlightthickness=0, bd=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self.task_container, orient="vertical", command=self.canvas.yview,
        )
        self.scroll_frame = tk.Frame(self.canvas, bg=Palette.BG)

        self.scroll_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw",
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.scrollbar.pack(side="right", fill="y", padx=(0, 2))

        self.empty_label = tk.Label(
            self.scroll_frame, text="暂无待办", font=UI_FONT_S,
            bg=Palette.BG, fg=Palette.MUTED,
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Web 共享开关
        self.web_frame = tk.Frame(self.root, bg=Palette.BG)
        self.web_frame.pack(fill="x", side="bottom", padx=28, pady=(8, 20))

        self.web_line = tk.Frame(self.web_frame, height=1, bg=Palette.LINE)
        self.web_line.pack(fill="x", pady=(0, 12))

        self.web_toggle = WebToggle(self.web_frame, on_toggle=self._on_web_toggle)
        self.web_toggle.pack(fill="x")

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_web_toggle(self, on: bool):
        if on:
            self.web_server.start()
            ip = get_lan_ip()
            url = f"http://{ip}:{WEB_PORT}"
            self.web_toggle.url_label.configure(text=url)
        else:
            self.web_server.stop()
            self.web_toggle.url_label.configure(text="")

    def add_todo(self):
        text = self.entry.get().strip()
        if not text:
            return
        todo = {
            "text": text,
            "done": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.todos.insert(0, todo)
        self.entry.delete(0, "end")
        self._persist_and_render()

    def _on_todo_change(self, delete_index: Optional[int] = None):
        if delete_index is not None:
            del self.todos[delete_index]
        self._persist_and_render()

    def _persist_and_render(self):
        save_todos(self.todos)
        self._render_tasks()
        self.entry.focus_set()

    def _render_tasks(self):
        for row in self.task_rows:
            row.destroy()
        self.task_rows.clear()

        if not self.todos:
            self.empty_label.pack(pady=60)
            self.count_label.configure(text="")
            return

        self.empty_label.pack_forget()

        done_count = sum(1 for t in self.todos if t.get("done"))
        total = len(self.todos)
        self.count_label.configure(text=f"{done_count}/{total} 已完成")

        for i, todo in enumerate(self.todos):
            row = TaskRow(self.scroll_frame, todo, i, self._on_todo_change)
            row.pack(fill="x")
            self.task_rows.append(row)

    def _delete_last_done(self):
        for i in range(len(self.todos) - 1, -1, -1):
            if self.todos[i].get("done"):
                del self.todos[i]
                self._persist_and_render()
                return

    def _focus_input(self):
        self.entry.focus_set()


# ── 入口 ──────────────────────────────────────────────────
if __name__ == "__main__":
    Palette.detect()
    TodoApp()
