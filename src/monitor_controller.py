import logging
import math
import time
from PySide6.QtCore import QRectF, QTimer
from PySide6.QtGui import QPainter
from .animation import Animation
from .assets import Assets
from .ball import draw_ball
from .hoop import Layout
from .overlay import Overlay
from .screen_geometry import ScreenArea
from .state_machine import StateMachine

class MonitorController:
    """One timer, one FSM and three tightly bounded windows per screen."""
    def __init__(self, screen, cfg, assets=None):
        self.screen, self.cfg = screen, cfg
        self.assets = assets or Assets(cfg)
        self.animation = Animation(self.assets)
        self.area = ScreenArea.from_screen(screen)
        self.layout = Layout.create(self.area, cfg, self.assets.hoop_meta)
        self.machine = self.make_machine()
        self.pet_window = Overlay(self.paint_pet, cfg.always_on_top)
        self.ball_window = Overlay(self.paint_ball, cfg.always_on_top)
        self.hoop_window = Overlay(self.paint_hoop, cfg.always_on_top)
        self.windows = (self.hoop_window, self.pet_window, self.ball_window)
        self.paused = False
        self.last_tick = time.perf_counter()
        self.last_state = self.machine.state
        self.position_hoop()
        self.render()
        for window in self.windows:
            window.show()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(round(1000/cfg.fps))

    def make_machine(self):
        frames = self.assets.frames["pickup_ball"]
        frame = frames[len(frames)//2]
        unit = self.layout.pet_height/self.cfg.sprite_canvas[1]
        offset = (frame.hand[0]-frame.foot[0])*unit
        return StateMachine(self.layout, self.cfg, pickup_offset=offset)

    def select_frame(self):
        m = self.machine
        self.frame = self.animation.frame(m.animation_state, m.time, m.animation_phase)
        self.sprite_scale = self.layout.pet_height/self.cfg.sprite_canvas[1]
        return self.animation.hand(self.frame, m.x, self.area.floor, m.direction, self.sprite_scale)

    def tick(self):
        now = time.perf_counter()
        dt = min(0.25, now-self.last_tick)  # suspend/resume should not skip hours of animation
        self.last_tick = now
        if self.paused:
            return
        remaining = dt
        while remaining > 1e-9:
            step = min(1/120, remaining)
            self.machine.update(step, self.select_frame())
            remaining -= step
        if self.machine.state != self.last_state:
            logging.debug("%s: %s", self.screen.name(), self.machine.state.value)
            self.last_state = self.machine.state
        self.render()

    def position_hoop(self):
        l = self.layout
        self.hoop_window.setGeometry(math.floor(l.hoop_x), math.floor(l.hoop_y), math.ceil(l.hoop_width+1), math.ceil(l.hoop_height+1))
        self.hoop_window.update()

    def render(self):
        m, l = self.machine, self.layout
        m.hand = self.select_frame()
        m.update_attached_ball()
        frame = self.frame
        unit = self.sprite_scale
        if m.direction > 0:
            left = m.x-frame.foot[0]*unit
        else:
            left = m.x-(frame.pixmap.width()-frame.foot[0])*unit
        top = l.area.floor-frame.foot[1]*unit
        self.pet_window.setGeometry(math.floor(left)-1, math.floor(top)-1,
                                    math.ceil(frame.pixmap.width()*unit)+2,
                                    math.ceil(frame.pixmap.height()*unit)+2)
        d = l.ball_radius*2
        self.ball_window.setGeometry(math.floor(m.ball.x-d), math.floor(m.ball.y-d), math.ceil(d*2+1), math.ceil(d*2+1))
        self.pet_window.update()
        self.ball_window.update()

    def paint_pet(self, p):
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        m = self.machine
        self.animation.draw(p, self.frame, m.x-self.pet_window.x(), self.area.floor-self.pet_window.y(), m.direction, self.sprite_scale)

    def paint_ball(self, p):
        b = self.machine.ball
        d = self.layout.ball_radius*2
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.translate(b.x-self.ball_window.x()-d, b.y-self.ball_window.y()-d)
        draw_ball(p, self.assets.ball, d, b.rotation, b.squash)

    def paint_hoop(self, p):
        l = self.layout
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.drawPixmap(QRectF(l.hoop_x-self.hoop_window.x(), l.hoop_y-self.hoop_window.y(), l.hoop_width, l.hoop_height), self.assets.hoop, QRectF(self.assets.hoop.rect()))

    def relayout(self, *_):
        area = ScreenArea.from_screen(self.screen)
        if area != self.area:
            self.area = area
            self.layout = Layout.create(area, self.cfg, self.assets.hoop_meta)
            self.machine = self.make_machine()
            self.last_state = self.machine.state
            self.position_hoop()
            self.render()

    def set_paused(self, paused):
        self.paused = paused
        self.last_tick = time.perf_counter()
        if paused:
            self.timer.stop()
        else:
            self.timer.start(round(1000/self.cfg.fps))

    def reset(self):
        self.machine.reset()
        self.last_tick = time.perf_counter()
        self.render()

    def close(self):
        self.timer.stop()
        for window in self.windows:
            window.close()
            window.deleteLater()
