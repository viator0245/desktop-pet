"""Native Windows smoke check. Run on a real Windows desktop, not offscreen."""
import ctypes
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
if sys.platform != 'win32':
    raise SystemExit('This check requires a Windows 10/11 desktop.')
from ctypes import wintypes
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from src.app import AppController
from src.config import Config
from src.windows_taskbar import taskbar_auto_hide

app=QApplication([])
app.setQuitOnLastWindowClosed(False)
if app.platformName() != 'windows':
    raise SystemExit('Use native Qt Windows platform; unset QT_QPA_PLATFORM.')
controller=AppController(app,Config())
user=ctypes.WinDLL('user32',use_last_error=True)
get=user.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p)==8 else user.GetWindowLongW
get.argtypes=[wintypes.HWND,ctypes.c_int]
get.restype=ctypes.c_ssize_t


def native_check():
    report=[]
    for screen,monitor in controller.monitors.items():
        styles=[]
        for window in monitor.windows:
            hwnd=int(window.winId())
            exstyle=get(hwnd,-20)
            style=get(hwnd,-16)
            expected=0x80000|0x20|0x80|0x08000000
            if controller.cfg.always_on_top:
                expected |= 0x8
            assert exstyle & expected == expected, f'Missing overlay styles: {exstyle:#x}'
            assert not style & 0x00C00000, 'Window caption must be absent'
            styles.append(hex(exstyle))
        auto=taskbar_auto_hide()
        rectangle=screen.geometry() if auto else screen.availableGeometry()
        assert monitor.area.floor == rectangle.y()+rectangle.height()
        report.append({'screen':screen.name(),'auto_hide':auto,'floor_y_logical':monitor.area.floor,'overlay_ex_styles':styles})
    print(json.dumps(report,indent=2))
    print('Native window styles and floor policy passed. Check actual mouse passthrough and hotplug visually.')


def check():
    try:
        native_check()
    except Exception:
        import traceback
        traceback.print_exc()
        app.exit(1)
    else:
        app.quit()

QTimer.singleShot(1500,check)
sys.exit(app.exec())
