"""Win32 calls use pointer-sized signatures; Qt positions stay in logical pixels."""
import ctypes
import sys
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND),
                ("uCallbackMessage", wintypes.UINT), ("uEdge", wintypes.UINT),
                ("rc", wintypes.RECT), ("lParam", ctypes.c_ssize_t)]


def taskbar_auto_hide():
    if not IS_WINDOWS:
        return False
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    fn = shell.SHAppBarMessage
    fn.argtypes = [wintypes.DWORD, ctypes.POINTER(APPBARDATA)]
    fn.restype = ctypes.c_size_t
    data = APPBARDATA()
    data.cbSize = ctypes.sizeof(data)
    return bool(fn(0x00000004, ctypes.byref(data)) & 0x00000001)  # GETSTATE, AUTOHIDE


def apply_overlay_style(hwnd, always_on_top=True):
    if not IS_WINDOWS:
        return
    user = ctypes.WinDLL("user32", use_last_error=True)
    get = user.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.GetWindowLongW
    set_ = user.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.SetWindowLongW
    get.argtypes = [wintypes.HWND, ctypes.c_int]
    get.restype = ctypes.c_ssize_t
    set_.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    set_.restype = ctypes.c_ssize_t
    flags = get(hwnd, -20) | 0x80000 | 0x20 | 0x80 | 0x08000000
    # LAYERED | TRANSPARENT | TOOLWINDOW | NOACTIVATE
    ctypes.set_last_error(0)
    set_(hwnd, -20, flags)
    if ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    pos = user.SetWindowPos
    pos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                    ctypes.c_int, ctypes.c_int, wintypes.UINT]
    pos.restype = wintypes.BOOL
    if not pos(hwnd, -1 if always_on_top else -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010):
        raise ctypes.WinError(ctypes.get_last_error())
