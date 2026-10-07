import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from .config import asset_root
from .pet import STATES, draw_placeholder, hand_anchor

@dataclass
class Frame:
    pixmap: QPixmap
    foot: tuple
    hand: tuple

class Assets:
    def __init__(self, cfg, root=None):
        self.cfg = cfg
        self.root = Path(root) if root else asset_root()
        metadata_path = self.root / "sakuragi" / "metadata.json"
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        self.frames = {}
        for state in STATES:
            self.frames[state] = self.load_frames(state)
        self.ball = self.read_pixmap(self.root / "basketball.png") or self.make_ball()
        self.hoop = self.read_pixmap(self.root / "hoop" / "hoop.png") or self.make_hoop()
        path = self.root / "hoop" / "metadata.json"
        self.hoop_meta = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.validate_hoop()

    @staticmethod
    def read_pixmap(path):
        if not path.exists():
            return None
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            raise ValueError(f"Invalid image: {path}")
        if not pixmap.hasAlphaChannel():
            logging.warning("Image has no alpha channel: %s", path)
        return pixmap

    @staticmethod
    def anchor(value, name):
        if not isinstance(value, (tuple, list)) or len(value) != 2 or any(not isinstance(v, (float, int)) or not math.isfinite(v) for v in value):
            raise ValueError(f"Invalid {name} anchor: {value}")
        return tuple(value)

    def load_frames(self, state):
        paths = sorted((self.root / "sakuragi" / state).glob("*.png"))
        result = []
        for path in paths:
            pixmap = self.read_pixmap(path)
            meta = self.metadata.get("frames", {}).get(f"{state}/{path.name}", {})
            foot = self.anchor(meta.get("foot_anchor", self.metadata.get("default_foot_anchor", self.cfg.sprite_foot_anchor)), "foot")
            hand = self.anchor(meta.get("hand_anchor", self.metadata.get("default_hand_anchor", [177, 159])), "hand")
            if not 0 <= foot[0] <= pixmap.width() or not 0 <= foot[1] <= pixmap.height():
                raise ValueError(f"Foot anchor outside image: {path}")
            result.append(Frame(pixmap, foot, hand))
        if result:
            return result
        for i in range(12):
            phase = i/11 if state in ("pickup_ball", "shoot_prep", "shoot_release") else i/12
            pixmap = QPixmap(256, 256)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            draw_placeholder(painter, state, phase)
            painter.end()
            result.append(Frame(pixmap, (128, 256), hand_anchor(state, phase)))
        return result

    def validate_hoop(self):
        meta = self.hoop_meta
        canvas = self.anchor(meta.get("canvas", [150, 230]), "hoop canvas")
        foot = self.anchor(meta.get("floor_anchor", [75, 230]), "hoop floor")
        rim = self.anchor(meta.get("rim_center", [48, 73]), "rim")
        radius = meta.get("rim_radius", 20)
        board = meta.get("backboard_x", 95)
        if min(canvas) <= 0 or not 0 <= foot[1] <= canvas[1] or not 0 <= rim[0] <= canvas[0] or not 0 <= rim[1] < canvas[1]:
            raise ValueError("Invalid hoop geometry metadata")
        if not isinstance(radius, (int, float)) or not math.isfinite(radius) or radius <= 10:
            raise ValueError("rim_radius must exceed ball radius (10 canvas units)")
        if not isinstance(board, (int, float)) or not math.isfinite(board) or not rim[0]+radius <= board <= canvas[0]:
            raise ValueError("backboard_x must be right of the rim")

    def make_ball(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#6b3920"), 3))
        p.setBrush(QColor("#f28b32"))
        p.drawEllipse(QRectF(2, 2, 60, 60))
        p.drawLine(32, 3, 32, 61)
        p.drawLine(3, 32, 61, 32)
        p.drawArc(QRectF(-17, 3, 50, 58), -80*16, 160*16)
        p.drawArc(QRectF(31, 3, 50, 58), 100*16, 160*16)
        p.end()
        return pixmap

    def make_hoop(self):
        pixmap = QPixmap(150, 230)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#293b56"), 4))
        p.setBrush(QColor("#5b7086"))
        p.drawRoundedRect(QRectF(107, 54, 10, 169), 3, 3)
        p.drawRoundedRect(QRectF(75, 219, 67, 9), 3, 3)
        p.setBrush(QColor(224, 243, 255, 150))
        p.drawRoundedRect(QRectF(91, 6, 51, 85), 4, 4)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor("#ebeff7"), 2))
        p.drawRect(QRectF(95, 45, 33, 27))
        # White net tapers below the orange rim.
        for x in range(29, 70, 10):
            p.drawLine(QPointF(x, 75), QPointF(48+(x-48)*0.5, 108))
        p.drawLine(QPointF(32, 87), QPointF(64, 87))
        p.drawLine(QPointF(37, 99), QPointF(59, 99))
        p.setPen(QPen(QColor("#e97934"), 4))
        p.drawLine(QPointF(69, 73), QPointF(96, 73))
        p.drawEllipse(QRectF(28, 68, 40, 10))
        p.end()
        return pixmap
