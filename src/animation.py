"""A stable foot pivot; per-frame metadata also drives the separate ball attachment."""
from PySide6.QtCore import QPointF

class Animation:
    def __init__(self, assets):
        self.assets = assets

    def frame(self, state, time, phase=None):
        frames = self.assets.frames.get(state, self.assets.frames["idle"])
        if phase is None:
            index = int(time*self.assets.cfg.sprite_fps*self.assets.cfg.animation_speed) % len(frames)
        else:
            index = min(len(frames)-1, int(max(0, min(1, phase))*len(frames)))
        return frames[index]

    def draw(self, painter, frame, foot_x, foot_y, direction, scale):
        painter.save()
        painter.translate(foot_x, foot_y)
        painter.scale(direction*scale, scale)
        painter.drawPixmap(QPointF(-frame.foot[0], -frame.foot[1]), frame.pixmap)
        painter.restore()

    def hand(self, frame, foot_x, floor, direction, scale):
        return (foot_x + direction*(frame.hand[0]-frame.foot[0])*scale,
                floor + (frame.hand[1]-frame.foot[1])*scale)
