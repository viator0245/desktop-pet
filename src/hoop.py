from dataclasses import dataclass
from .screen_geometry import ScreenArea
from .config import Config

@dataclass(frozen=True)
class Layout:
    area: ScreenArea
    scale: float
    hoop_x: float
    hoop_y: float
    hoop_width: float
    hoop_height: float
    rim_x: float
    rim_y: float
    rim_radius: float
    backboard_x: float
    start_x: float
    stop_x: float
    pet_width: float
    pet_height: float
    ball_radius: float
    landing_x: float

    @classmethod
    def create(cls, area, cfg, hoop_meta=None):
        meta = hoop_meta or {}
        canvas = meta.get("canvas", [150, 230])
        anchor = meta.get("floor_anchor", [75, 230])
        rim = meta.get("rim_center", [48, 73])
        radius = meta.get("rim_radius", 20)
        board = meta.get("backboard_x", 95)
        # Fit all objects and the trajectory on narrow/short screens.
        s = min(cfg.scale, area.width / 600, area.height / 600)
        s = max(0.02, s)
        w, h = canvas[0] * s, canvas[1] * s
        hx = area.right - w - 12 * s
        hy = area.floor - anchor[1] * s
        pet_h = cfg.sprite_display_height * s
        pet_w = cfg.sprite_canvas[0] / cfg.sprite_canvas[1] * pet_h
        stop = hx - cfg.safe_margin * s - pet_w / 2
        start = max(area.left + pet_w / 2 + 12 * s, stop - cfg.patrol_width * s)
        stop = max(start, stop)
        rim_x, rim_y = hx + rim[0]*s, hy + rim[1]*s
        return cls(area, s, hx, hy, w, h, rim_x, rim_y, radius*s,
                   hx + board*s, start, stop, pet_w, pet_h, 10*s, rim_x)
