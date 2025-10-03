# ------------------ Utilities ------------------
import subprocess
import platform
import json
import ctypes
from PySide6 import QtWidgets
from config import *

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    # default structure
    return {'apps': [], 'templates': {}}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        QtWidgets.QMessageBox.warning(None, 'Save error', f'Failed to save config: {e}')


def is_windows():
    return platform.system() == 'Windows'


def launch_process(path, args: list, as_admin=False, use_powershell_elevated=False):
    """Launch process. If use_powershell_elevated is True on Windows, open an elevated PowerShell window
    and pass the assembled command to it using -NoExit -Command "<cmd>" so the window stays open after execution.
    """
    cmd = [path] + args if path else args
    try:
        if is_windows() and use_powershell_elevated:
            assembled = ' '.join([str(p) for p in cmd])
            ps_cmd = assembled.replace('"', '\"')
            params = f'-NoExit -Command "{ps_cmd}"'
            ctypes.windll.shell32.ShellExecuteW(None, 'runas', 'powershell.exe', params, None, 1)
            return True
        elif is_windows() and as_admin and path:
            params = ' '.join([f'"{p}"' for p in args])
            ctypes.windll.shell32.ShellExecuteW(None, 'runas', str(path), params, None, 1)
            return True
        else:
            if path:
                subprocess.Popen([path] + args)
            else:
                subprocess.Popen(args)
            return True
    except Exception as e:
        QtWidgets.QMessageBox.warning(None, 'Launch failed', f'Failed to launch: {e}')
        return False

