import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QObject, QRect, Signal, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication
from src.animation import Animation
from src.assets import Assets
from src.config import Config
from src.monitor_controller import MonitorController
from src.screen_geometry import ScreenArea
from src.state_machine import State
from src.app import AppController

APP = QApplication.instance() or QApplication([])
APP.setQuitOnLastWindowClosed(False)

class FakeScreen(QObject):
    geometryChanged = Signal(QRect)
    availableGeometryChanged = Signal(QRect)
    logicalDotsPerInchChanged = Signal(float)
    def __init__(self, x=0):
        super().__init__()
        self.full = QRect(x,0,1280,800)
        self.available = QRect(x,0,1280,752)
    def geometry(self): return self.full
    def availableGeometry(self): return self.available
    def name(self): return 'test-display'

class GuiTests(unittest.TestCase):
    def setUp(self):
        patcher=patch("src.screen_geometry.taskbar_auto_hide", return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    @classmethod
    def setUpClass(cls):
        cls.assets=Assets(Config())

    def test_taskbar_floor_policy_including_temporary_auto_hide_reveal(self):
        screen=FakeScreen(-1280)
        with patch('src.screen_geometry.taskbar_auto_hide',return_value=False):
            self.assertEqual(ScreenArea.from_screen(screen).floor,752)
        with patch('src.screen_geometry.taskbar_auto_hide',return_value=True):
            before=ScreenArea.from_screen(screen)
            screen.available=QRect(-1280,0,1280,710)
            after=ScreenArea.from_screen(screen)
            self.assertEqual(before,after)
            self.assertEqual(after.floor,800)

    def test_transparent_windows_pause_reset_and_geometry_change(self):
        screen=FakeScreen()
        controller=MonitorController(screen,Config(),self.assets)
        try:
            for window in controller.windows:
                self.assertTrue(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
                for flag in (Qt.WindowType.FramelessWindowHint,Qt.WindowType.WindowTransparentForInput,Qt.WindowType.WindowStaysOnTopHint,Qt.WindowType.WindowDoesNotAcceptFocus):
                    self.assertTrue(window.windowFlags() & flag)
                self.assertLess(window.width()*window.height(),1280*800/10)
            controller.set_paused(True)
            before=(controller.machine.time,controller.machine.x,controller.machine.ball.rotation)
            controller.last_tick=time.perf_counter()-.1
            controller.tick()
            self.assertEqual(before,(controller.machine.time,controller.machine.x,controller.machine.ball.rotation))
            self.assertFalse(controller.timer.isActive())
            controller.set_paused(False)
            controller.last_tick=time.perf_counter()-.1
            controller.tick()
            self.assertGreater(controller.machine.time,before[0])
            screen.full=QRect(-1920,-300,1920,1080)
            screen.available=QRect(-1920,-300,1920,1032)
            controller.relayout()
            self.assertEqual(controller.area.floor,732)
            self.assertEqual(controller.machine.x,controller.layout.start_x)
            controller.reset()
            self.assertEqual(controller.machine.completed_laps,0)
        finally: controller.close()

    def test_hotplug_independent_monitor_and_asset_reload(self):
        controller=AppController(APP,Config())
        extra=FakeScreen(-1280)
        try:
            count=len(controller.monitors)
            controller.screen_added(extra)
            self.assertEqual(len(controller.monitors),count+1)
            monitors=list(controller.monitors.values())
            self.assertIsNot(monitors[0].machine,monitors[-1].machine)
            controller.set_paused(True)
            controller.reset()
            controller.reload()
            self.assertTrue(controller.paused)
            self.assertTrue(all(not m.timer.isActive() for m in controller.monitors.values()))
            controller.screen_added(extra)
            controller.screen_removed(extra)
            self.assertNotIn(extra,controller.monitors)
        finally:
            APP.screenAdded.disconnect(controller.screen_added)
            APP.screenRemoved.disconnect(controller.screen_removed)
            APP.aboutToQuit.disconnect(controller.close)
            controller.close()

    def test_custom_frames_and_anchors_flip_consistently(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            folder=root/'sakuragi'/'idle'
            folder.mkdir(parents=True)
            image=QImage(180,220,QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            image.setPixelColor(70,210,Qt.GlobalColor.red)
            image.save(str(folder/'01.png'))
            meta={'frames':{'idle/01.png':{'foot_anchor':[70,210],'hand_anchor':[130,110]}}}
            (root/'sakuragi'/'metadata.json').write_text(json.dumps(meta))
            assets=Assets(Config(),root)
            animation=Animation(assets)
            frame=animation.frame('idle',0)
            self.assertEqual(animation.hand(frame,500,800,1,.5),(530,750))
            self.assertEqual(animation.hand(frame,500,800,-1,.5),(470,750))
            self.assertEqual(len(assets.frames['idle']),1)
            self.assertEqual(len(assets.frames['reaction_success']),12)

    def test_custom_pickup_anchor_positions_the_character_before_attachment(self):
        from src.assets import Frame
        screen=FakeScreen()
        assets=Assets(Config())
        original=assets.frames['pickup_ball'][0]
        assets.frames['pickup_ball']=[Frame(original.pixmap,(128,256),(210,240))]
        c=MonitorController(screen,Config(move_speed=1000),assets)
        try:
            c.set_paused(True)
            m=c.machine
            m.ball.x=c.layout.rim_x
            m.ball.y=c.area.floor-c.layout.ball_radius
            m.ball.mode='grounded'
            m.transition(State.WALK_TO_BALL)
            for _ in range(1000):
                m.update(1/120)
                if m.state==State.PICKUP_BALL: break
            self.assertEqual(m.state,State.PICKUP_BALL)
            c.render()
            self.assertAlmostEqual(m.hand[0],m.ball.x)
        finally: c.close()

    def test_sprite_alpha_and_cached_frames(self):
        self.assertEqual(sum(len(v) for v in self.assets.frames.values()),84)
        for frames in self.assets.frames.values():
            for frame in frames:
                self.assertTrue(frame.pixmap.hasAlphaChannel())
                self.assertEqual(frame.pixmap.toImage().pixelColor(0,0).alpha(),0)
        self.assertTrue(self.assets.ball.hasAlphaChannel())
        self.assertTrue(self.assets.hoop.hasAlphaChannel())

if __name__=='__main__': unittest.main()
