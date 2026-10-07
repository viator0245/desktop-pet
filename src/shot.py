import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Projectile:
    x0: float
    y0: float
    vx: float
    vy: float
    gravity: float
    duration: float
    target_x: float
    target_y: float

    @classmethod
    def toward(cls, origin, target, scale, top):
        x0, y0 = origin
        tx, ty = target
        gravity = 500*scale
        apex = max(top+24*scale, min(y0, ty)-120*scale)
        if apex >= min(y0, ty):
            apex = min(y0, ty)-max(1, 10*scale)
        up = math.sqrt(2*(y0-apex)/gravity)
        down = math.sqrt(2*(ty-apex)/gravity)
        duration = up+down
        return cls(x0, y0, (tx-x0)/duration, -gravity*up, gravity, duration, tx, ty)

    def position(self, time):
        t = min(max(time, 0), self.duration)
        return self.x0+self.vx*t, self.y0+self.vy*t+0.5*self.gravity*t*t

    def velocity(self, time):
        return self.vx, self.vy+self.gravity*min(time, self.duration)
