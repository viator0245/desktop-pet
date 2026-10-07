import sys
from . import startup
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

class Tray:
    def __init__(self, app, controller):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        p = QPainter(pixmap)
        p.setBrush(QColor("#ef8637"))
        p.drawEllipse(3, 3, 26, 26)
        p.drawLine(16, 3, 16, 29)
        p.end()
        self.icon = QSystemTrayIcon(QIcon(pixmap), app)
        self.icon.setToolTip("Sakuragi Desktop Pet")
        self.menu = QMenu()
        title = self.menu.addAction("Sakuragi Desktop Pet")
        title.setEnabled(False)
        self.menu.addSeparator()
        for label, callback in [("Pause", lambda: controller.set_paused(True)),
                                ("Resume", lambda: controller.set_paused(False)),
                                ("Reset Position", controller.reset),
                                ("Reload Assets", controller.reload),
                                ("Settings", controller.settings),
                                ("Exit", app.quit)]:
            action = QAction(label, self.menu)
            action.triggered.connect(callback)
            self.menu.addAction(action)
        startup_action = QAction("Run at Windows Startup", self.menu)
        startup_action.setCheckable(True)
        startup_action.setEnabled(sys.platform == "win32")
        startup_action.setChecked(startup.enabled())
        def toggle_startup(checked):
            from PySide6.QtWidgets import QMessageBox
            try:
                startup.set_enabled(checked)
            except OSError as exc:
                startup_action.setChecked(startup.enabled())
                QMessageBox.warning(None, "Startup setting failed", str(exc))
        startup_action.triggered.connect(toggle_startup)
        self.menu.insertAction(self.menu.actions()[-1], startup_action)
        self.icon.setContextMenu(self.menu)
        self.icon.show()
