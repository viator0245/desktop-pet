"""Optional tray-controlled Windows startup, scoped to the current user."""
import subprocess
import sys
from pathlib import Path
from .config import PROJECT_ROOT

NAME = "SakuragiDesktopPet"
KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def command():
    if getattr(sys, "frozen", False):
        args = [sys.executable]
    else:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        args = [str(pythonw if pythonw.exists() else sys.executable), str(PROJECT_ROOT / "main.py")]
    return subprocess.list2cmdline(args)


def enabled():
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as key:
            value, _ = winreg.QueryValueEx(key, NAME)
        return value == command()
    except OSError:
        return False


def set_enabled(value):
    if sys.platform != "win32":
        raise RuntimeError("Windows startup is available on Windows only")
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY) as key:
        if value:
            winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, command())
        else:
            try:
                winreg.DeleteValue(key, NAME)
            except FileNotFoundError:
                pass
