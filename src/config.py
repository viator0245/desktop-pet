import json
import math
import sys
from dataclasses import dataclass, fields
from pathlib import Path

BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
PROJECT_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else BUNDLE_ROOT

@dataclass(frozen=True)
class Config:
    scale: float = 1.0
    move_speed: float = 80.0
    fps: int = 30
    patrol_width: float = 700.0
    animation_speed: float = 1.0
    shot_make_probability: float = 0.5
    laps_before_shot: int = 3
    reaction_duration: float = 1.2
    always_on_top: bool = True
    sprite_canvas: tuple = (256, 256)
    sprite_display_height: float = 144.0
    sprite_fps: float = 10.0
    sprite_foot_anchor: tuple = (128, 256)
    safe_margin: float = 24.0

    @classmethod
    def load(cls, path=None):
        if path is not None:
            path = Path(path)
            if not path.is_file():
                raise FileNotFoundError(f"Config not found: {path}")
        else:
            external = PROJECT_ROOT / "config.json"
            path = external if external.is_file() else BUNDLE_ROOT / "config.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")
        cfg = cls(**data)
        for key in ("scale", "move_speed", "patrol_width", "animation_speed", "reaction_duration", "sprite_display_height", "sprite_fps"):
            value = getattr(cfg, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{key} must be a finite positive number")
        if not isinstance(cfg.fps, int) or isinstance(cfg.fps, bool) or not 1 <= cfg.fps <= 30:
            raise ValueError("fps must be an integer in 1..30")
        if not isinstance(cfg.laps_before_shot, int) or isinstance(cfg.laps_before_shot, bool) or cfg.laps_before_shot < 1:
            raise ValueError("laps_before_shot must be a positive integer")
        if not isinstance(cfg.shot_make_probability, (int, float)) or not 0 <= cfg.shot_make_probability <= 1:
            raise ValueError("shot_make_probability must be in 0..1")
        if not isinstance(cfg.always_on_top, bool):
            raise ValueError("always_on_top must be boolean")
        if not isinstance(cfg.safe_margin, (int, float)) or not math.isfinite(cfg.safe_margin) or cfg.safe_margin < 0:
            raise ValueError("safe_margin must be nonnegative")
        for key in ("sprite_canvas", "sprite_foot_anchor"):
            value = getattr(cfg, key)
            if not isinstance(value, (list, tuple)) or len(value) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
                raise ValueError(f"{key} must be a pair of finite numbers")
        if min(cfg.sprite_canvas) <= 0:
            raise ValueError("sprite_canvas must be positive")
        return cfg


def asset_root():
    external = PROJECT_ROOT / "assets"
    return external if external.is_dir() else BUNDLE_ROOT / "assets"
