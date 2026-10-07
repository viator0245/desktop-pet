"""Time-driven finite state machine, independent of GUI timers and monitors.

Ball physics runs concurrently with the character's reaction. State handlers are
small methods in a dispatch table, so no monolithic update conditional is needed.
"""
import math
import random
from collections import deque
from enum import Enum
from .ball import Ball
from .movement import approach
from .shot import Projectile

class State(str, Enum):
    IDLE = "idle"
    WALK_TO_HOOP = "walk_to_hoop"
    TURN_AT_HOOP = "turn_at_hoop"
    WALK_BACK = "walk_back"
    TURN_AT_START = "turn_at_start"
    SHOOT_PREP = "shoot_prep"
    SHOOT_RELEASE = "shoot_release"
    BALL_IN_FLIGHT = "ball_in_flight"
    SHOT_MADE = "shot_made"
    SHOT_MISSED = "shot_missed"
    REACTION_SUCCESS = "reaction_success"
    REACTION_MISS = "reaction_miss"
    BALL_FALLING = "ball_falling"
    BALL_BOUNCING = "ball_bouncing"
    WALK_TO_BALL = "walk_to_ball"
    PICKUP_BALL = "pickup_ball"
    RETURN_TO_START = "return_to_start"

class StateMachine:
    def __init__(self, layout, cfg, rng=None, pickup_offset=None):
        self.layout, self.cfg = layout, cfg
        self.rng = rng or random.Random()
        self.pickup_offset = pickup_offset if pickup_offset is not None else 49*layout.pet_height/cfg.sprite_canvas[1]
        self.handlers = {
            State.IDLE: self.idle,
            State.WALK_TO_HOOP: self.walk_to_hoop,
            State.TURN_AT_HOOP: self.turn_at_hoop,
            State.WALK_BACK: self.walk_back,
            State.TURN_AT_START: self.turn_at_start,
            State.SHOOT_PREP: self.shoot_prep,
            State.SHOOT_RELEASE: self.shoot_release,
            State.BALL_IN_FLIGHT: self.ball_in_flight,
            State.SHOT_MADE: self.shot_made,
            State.SHOT_MISSED: self.shot_missed,
            State.REACTION_SUCCESS: self.reaction,
            State.REACTION_MISS: self.reaction,
            State.BALL_FALLING: self.wait_for_ball,
            State.BALL_BOUNCING: self.wait_for_ball,
            State.WALK_TO_BALL: self.walk_to_ball,
            State.PICKUP_BALL: self.pickup_ball,
            State.RETURN_TO_START: self.return_to_start,
        }
        self.reset()

    def reset(self):
        self.x = self.layout.start_x
        self.direction = 1
        self.time = self.elapsed = 0.0
        self.completed_laps = self.completed_cycles = self.shots = 0
        self.state = State.IDLE
        self.history = deque([self.state.value], maxlen=128)
        self.ball = Ball()
        self.made = None
        self.projectile = None
        self.shot_laps = deque(maxlen=32)
        self.pickup_attached = False
        self.hand = self.default_hand()
        self.update_attached_ball()

    def default_hand(self):
        l = self.layout
        unit = l.pet_height / self.cfg.sprite_canvas[1]
        return self.x+self.direction*49*unit, l.area.floor-97*unit

    def transition(self, state):
        self.state, self.elapsed = state, 0.0
        self.history.append(state.value)

    @property
    def animation_state(self):
        return {
            State.WALK_TO_HOOP: "walk_dribble", State.WALK_BACK: "walk_dribble",
            State.RETURN_TO_START: "walk_dribble", State.WALK_TO_BALL: "walk_dribble",
            State.SHOOT_PREP: "shoot_prep", State.SHOOT_RELEASE: "shoot_release",
            State.BALL_IN_FLIGHT: "shoot_release",
            State.SHOT_MADE: "reaction_success", State.REACTION_SUCCESS: "reaction_success",
            State.SHOT_MISSED: "reaction_miss", State.REACTION_MISS: "reaction_miss",
            State.PICKUP_BALL: "pickup_ball",
        }.get(self.state, "idle")

    @property
    def animation_phase(self):
        durations = {State.SHOOT_PREP: 0.7, State.SHOOT_RELEASE: 0.35, State.PICKUP_BALL: 1.1}
        if self.state in durations:
            return min(1, self.elapsed/durations[self.state])
        if self.state == State.BALL_IN_FLIGHT:
            return 1.0
        return None

    def update(self, dt, hand=None):
        # Fixed/subdivided logical timesteps preserve bounce contacts after timer jitter.
        if dt < 0 or not math.isfinite(dt):
            raise ValueError("dt must be finite and nonnegative")
        self.hand = hand if hand is not None else self.default_hand()
        self.time += dt
        self.elapsed += dt
        self.update_loose_ball(dt)
        self.handlers[self.state](dt)
        self.update_attached_ball()
        if self.ball.mode != "grounded":
            self.ball.rotation = (self.ball.rotation+240*dt) % 360

    def move(self, target, dt):
        self.direction = 1 if target >= self.x else -1
        self.x, arrived = approach(self.x, target, self.cfg.move_speed*self.layout.scale*dt)
        return arrived

    def idle(self, dt):
        if self.elapsed >= 0.3:
            self.ball.mode = "dribbling"
            self.transition(State.WALK_TO_HOOP)

    def walk_to_hoop(self, dt):
        if self.move(self.layout.stop_x, dt):
            self.transition(State.TURN_AT_HOOP)

    def turn_at_hoop(self, dt):
        if self.elapsed >= 0.2:
            self.direction = -1
            self.transition(State.WALK_BACK)

    def walk_back(self, dt):
        if self.move(self.layout.start_x, dt):
            self.completed_laps += 1
            self.transition(State.TURN_AT_START)

    def turn_at_start(self, dt):
        if self.elapsed >= 0.25:
            self.direction = 1
            if self.completed_laps >= self.cfg.laps_before_shot:
                self.ball.mode = "held"
                self.transition(State.SHOOT_PREP)
            else:
                self.transition(State.WALK_TO_HOOP)

    def shoot_prep(self, dt):
        if self.elapsed >= 0.7:
            self.transition(State.SHOOT_RELEASE)

    def shoot_release(self, dt):
        if self.elapsed < 0.35:
            return
        l = self.layout
        self.made = self.rng.random() < self.cfg.shot_make_probability
        # Miss is a real rim-edge contact; incoming and rebound velocities differ.
        tx = l.rim_x if self.made else l.rim_x-l.rim_radius-l.ball_radius
        ty = l.rim_y if self.made else l.rim_y-l.ball_radius
        origin = self.hand
        self.projectile = Projectile.toward(origin, (tx, ty), l.scale, l.area.top)
        self.ball.x, self.ball.y = origin
        self.ball.mode = "shot"
        self.shots += 1
        self.shot_laps.append(self.completed_laps)
        self.transition(State.BALL_IN_FLIGHT)

    def ball_in_flight(self, dt):
        self.ball.x, self.ball.y = self.projectile.position(self.elapsed)
        if self.elapsed >= self.projectile.duration:
            _, impact_vy = self.projectile.velocity(self.projectile.duration)
            self.ball.mode = "falling"
            self.ball.bounces = 0
            if self.made:
                self.ball.vx, self.ball.vy = 0, impact_vy*0.35
                self.transition(State.SHOT_MADE)
            else:
                self.ball.vx, self.ball.vy = -85*self.layout.scale, -impact_vy*0.42
                self.transition(State.SHOT_MISSED)

    def shot_made(self, dt):
        self.transition(State.REACTION_SUCCESS)

    def shot_missed(self, dt):
        self.transition(State.REACTION_MISS)

    def reaction(self, dt):
        if self.elapsed >= self.cfg.reaction_duration:
            self.wait_for_ball(dt)

    def wait_for_ball(self, dt):
        if self.ball.mode == "grounded":
            self.transition(State.WALK_TO_BALL)
        elif self.ball.mode == "bouncing":
            if self.state != State.BALL_BOUNCING:
                self.transition(State.BALL_BOUNCING)
        elif self.state != State.BALL_FALLING:
            self.transition(State.BALL_FALLING)

    def walk_to_ball(self, dt):
        # Offset aligns pickup hand with ball instead of teleporting it to the torso.
        target = self.ball.x-self.pickup_offset
        if self.move(target, dt):
            self.direction = 1
            self.pickup_attached = False
            self.transition(State.PICKUP_BALL)

    def pickup_ball(self, dt):
        if self.elapsed >= 0.55 and not self.pickup_attached:
            self.pickup_attached = True
            self.ball.mode = "held"
        if self.elapsed >= 1.1:
            self.direction = -1
            self.ball.mode = "dribbling"
            self.transition(State.RETURN_TO_START)

    def return_to_start(self, dt):
        if self.move(self.layout.start_x, dt):
            self.completed_laps = 0
            self.completed_cycles += 1
            self.direction = 1
            self.transition(State.TURN_AT_START)

    def update_attached_ball(self):
        l, b = self.layout, self.ball
        if b.mode == "dribbling":
            # A quadratic flight between contacts. Vertical velocity reverses at floor.
            phase = (self.time*1.7*self.cfg.animation_speed) % 1
            height = l.pet_height*0.36
            b.x = self.hand[0]
            b.y = l.area.floor-l.ball_radius-height*4*phase*(1-phase)
            b.squash = 0.78 if phase < 0.05 or phase > 0.95 else 1.0
            if b.squash < 1:
                b.y = l.area.floor-l.ball_radius*b.squash
        elif b.mode == "held":
            b.x, b.y = self.hand
            b.squash = 1
        # Bounds on every ball mode, including a custom hand anchor at screen edges.
        b.x = max(l.area.left+l.ball_radius, min(l.area.right-l.ball_radius, b.x))
        b.y = max(l.area.top+l.ball_radius, min(l.area.floor-l.ball_radius*b.squash, b.y))

    def update_loose_ball(self, dt):
        b, l = self.ball, self.layout
        if b.mode not in ("falling", "bouncing"):
            return
        # Sideways rebound is damped back toward the basket's landing zone.
        if not self.made:
            b.vx += (12*(l.landing_x-b.x)-5*b.vx)*dt
        b.vy += 650*l.scale*dt
        b.x += b.vx*dt
        b.y += b.vy*dt
        floor = l.area.floor-l.ball_radius
        b.squash = 1
        if b.y >= floor and b.vy > 0:
            b.y = floor
            b.bounces += 1
            if b.bounces <= 2:
                b.vy = -b.vy*(0.33 if b.bounces == 1 else 0.28)
                b.vx *= 0.45
                b.mode = "bouncing"
            else:
                b.vx = b.vy = 0
                b.mode = "grounded"
