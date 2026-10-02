import os
import sys
import winreg
from pathlib import Path

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "HandsfreeApexCaliberLabs"


def set_run_at_startup(enable: bool) -> bool:
    """Configures Handsfree to launch automatically when user logs in."""
    try:
        # Determine executable path
        if getattr(sys, "frozen", False):
            exe_path = f'"{sys.executable}" --background'
        else:
            python_exe = sys.executable
            main_script = str(Path(__file__).resolve().parent.parent / "main.py")
            exe_path = f'"{python_exe}" "{main_script}" --background'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
        with key:
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"[Autostart] Error setting startup registry: {e}")
        return False


def is_run_at_startup_enabled() -> bool:
    """Checks if startup registry entry exists."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        with key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
