import logging
import json
from dataclasses import asdict
from pathlib import Path
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox
from .config import Config, PROJECT_ROOT
from .assets import Assets
from .monitor_controller import MonitorController
from .tray import Tray

class AppController:
    def __init__(self, app, cfg, config_path=None):
        self.app, self.cfg = app, cfg
        self.config_path = Path(config_path) if config_path else PROJECT_ROOT / "config.json"
        self.assets = Assets(cfg)
        self.monitors = {}
        self.paused = False
        self.sync_screens()
        app.screenAdded.connect(self.screen_added)
        app.screenRemoved.connect(self.screen_removed)
        self.geometry_timer = QTimer()
        self.geometry_timer.timeout.connect(self.refresh_geometry)
        self.geometry_timer.start(1000)  # auto-hide setting changes also detected
        self.tray = Tray(app, self)
        app.aboutToQuit.connect(self.close)

    def sync_screens(self):
        for screen in self.app.screens():
            self.screen_added(screen)

    def screen_added(self, screen):
        if screen in self.monitors:
            return
        controller = MonitorController(screen, self.cfg, self.assets)
        self.monitors[screen] = controller
        controller.set_paused(self.paused)
        screen.geometryChanged.connect(controller.relayout)
        screen.availableGeometryChanged.connect(controller.relayout)
        screen.logicalDotsPerInchChanged.connect(controller.relayout)
        logging.info("Monitor added: %s", screen.name())

    def screen_removed(self, screen):
        controller = self.monitors.pop(screen, None)
        if controller:
            for signal in (screen.geometryChanged, screen.availableGeometryChanged, screen.logicalDotsPerInchChanged):
                try:
                    signal.disconnect(controller.relayout)
                except (RuntimeError, TypeError):
                    pass
            controller.close()

    def refresh_geometry(self):
        for controller in list(self.monitors.values()):
            controller.relayout()

    def set_paused(self, paused):
        self.paused = paused
        for controller in self.monitors.values():
            if hasattr(controller, "set_paused"):
                controller.set_paused(paused)

    def reset(self):
        for controller in self.monitors.values():
            if hasattr(controller, "reset"):
                controller.reset()
            else:
                controller.relayout()

    def reload(self):
        try:
            cfg = Config.load(self.config_path)
            assets = Assets(cfg)
            self.cfg = cfg
            self.assets = assets
            for screen in list(self.monitors):
                self.screen_removed(screen)
            self.sync_screens()
            self.set_paused(self.paused)
        except Exception as exc:
            logging.exception("Reload failed")
            QMessageBox.warning(None, "Reload failed", str(exc))

    def settings(self):
        try:
            if not self.config_path.exists():
                self.config_path.write_text(json.dumps(asdict(self.cfg), indent=2), encoding="utf-8")
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.config_path.resolve()))):
                QMessageBox.information(None, "Settings", f"Edit this file and choose Reload Assets:\n{self.config_path}")
        except OSError as exc:
            QMessageBox.warning(None, "Settings", str(exc))

    def close(self):
        self.geometry_timer.stop()
        for controller in list(self.monitors.values()):
            controller.close()
        self.tray.icon.hide()


def run(config_path=None, smoke_seconds=0):
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    try:
        cfg = Config.load(config_path)
        controller = AppController(app, cfg, config_path)
    except Exception as exc:
        logging.exception("Startup failed")
        QMessageBox.critical(None, "Sakuragi Desktop Pet", str(exc))
        return 1
    if smoke_seconds > 0:
        QTimer.singleShot(int(smoke_seconds*1000), app.quit)
    return app.exec()
