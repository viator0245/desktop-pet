from dataclasses import dataclass
from PySide6.QtCore import QRectF

@dataclass
class Ball:
    x: float = 0
    y: float = 0
    vx: float = 0
    vy: float = 0
    mode: str = "held"
    rotation: float = 0
    squash: float = 1
    bounces: int = 0


def draw_ball(painter, pixmap, diameter, rotation, squash):
    painter.save()
    painter.translate(diameter, diameter)
    painter.scale(1 + (1-squash)*0.3, squash)
    painter.rotate(rotation)
    painter.drawPixmap(QRectF(-diameter/2, -diameter/2, diameter, diameter), pixmap, QRectF(pixmap.rect()))
    painter.restore()
