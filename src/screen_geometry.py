from dataclasses import dataclass
from .windows_taskbar import taskbar_auto_hide

@dataclass(frozen=True)
class ScreenArea:
    left: float
    top: float
    width: float
    height: float

    @property
    def right(self):
        return self.left + self.width

    @property
    def floor(self):
        return self.top + self.height  # exclusive bottom edge, no physical/logical pixel mixing

    @classmethod
    def from_screen(cls, screen, auto_hide=None):
        if auto_hide is None:
            auto_hide = taskbar_auto_hide()
        rect = screen.geometry() if auto_hide else screen.availableGeometry()
        return cls(rect.x(), rect.y(), rect.width(), rect.height())
