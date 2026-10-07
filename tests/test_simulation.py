import math
import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from src.config import Config
from src.hoop import Layout
from src.screen_geometry import ScreenArea
from src.shot import Projectile
from src.state_machine import State, StateMachine

class SimulationTests(unittest.TestCase):
    def machine(self, probability=1, area=None):
        cfg = Config(move_speed=900, patrol_width=180, shot_make_probability=probability)
        area = area or ScreenArea(0,0,1920,1040)
        return StateMachine(Layout.create(area,cfg), cfg, random.Random(42))

    def run_cycle(self, m, cycles=2):
        transitions = []
        grounded = []
        impacts = []
        last = m.state
        for _ in range(50000):
            m.update(1/120)
            b, l = m.ball, m.layout
            self.assertTrue(math.isfinite(b.x) and math.isfinite(b.y))
            self.assertGreaterEqual(b.x, l.area.left+l.ball_radius-1e-6)
            self.assertLessEqual(b.x, l.area.right-l.ball_radius+1e-6)
            self.assertGreaterEqual(b.y, l.area.top+l.ball_radius-1e-6)
            self.assertLessEqual(b.y+b.squash*l.ball_radius, l.area.floor+1e-6)
            if m.state != last:
                transitions.append(m.state)
                last = m.state
                if last in (State.SHOT_MADE, State.SHOT_MISSED):
                    impacts.append((b.x,b.y,b.vx,b.vy))
                if last == State.WALK_TO_BALL:
                    grounded.append((b.x,b.y,b.bounces))
            if m.completed_cycles >= cycles:
                break
        self.assertEqual(m.completed_cycles, cycles)
        self.assertEqual(list(m.shot_laps), [3]*cycles)
        self.assertEqual(transitions.count(State.WALK_BACK), 3*cycles)
        self.assertEqual(transitions.count(State.PICKUP_BALL), cycles)
        self.assertEqual(m.completed_laps, 0)
        for x,y,bounces in grounded:
            self.assertGreaterEqual(x,m.layout.hoop_x)
            self.assertLessEqual(x,m.layout.hoop_x+m.layout.hoop_width)
            self.assertAlmostEqual(y,m.layout.area.floor-m.layout.ball_radius)
            self.assertEqual(bounces,3)  # two rebounds, third contact settles
        return transitions, impacts

    def test_made_complete_loops(self):
        m = self.machine(1)
        states, impacts = self.run_cycle(m)
        self.assertIn(State.REACTION_SUCCESS, states)
        self.assertNotIn(State.REACTION_MISS, states)
        for x,y,vx,vy in impacts:
            self.assertAlmostEqual(x,m.layout.rim_x)
            self.assertAlmostEqual(y,m.layout.rim_y)
            self.assertGreater(vy,0)

    def test_miss_collision_and_recovery(self):
        m = self.machine(0)
        states, impacts = self.run_cycle(m)
        self.assertIn(State.REACTION_MISS, states)
        self.assertNotIn(State.REACTION_SUCCESS, states)
        for x,y,vx,vy in impacts:
            self.assertAlmostEqual(x,m.layout.rim_x-m.layout.rim_radius-m.layout.ball_radius)
            self.assertLess(vx,0)
            self.assertLess(vy,0)

    def test_negative_origin_and_small_screens(self):
        for area in [ScreenArea(-1920,-250,1920,1040), ScreenArea(0,0,800,560), ScreenArea(1920,0,3840,2080)]:
            with self.subTest(area=area):
                self.run_cycle(self.machine(0,area),1)

    def test_default_three_laps_not_only_accelerated_configuration(self):
        cfg = Config()
        m = StateMachine(Layout.create(ScreenArea(0,0,1920,1040),cfg),cfg, random.Random(1))
        for _ in range(14000):
            m.update(1/120)
            if m.completed_cycles:
                break
        self.assertEqual(m.completed_cycles,1)
        self.assertEqual(list(m.shot_laps),[3])

    def test_seeded_random_outcomes_and_independent_monitors(self):
        a,b = self.machine(.5),self.machine(.5)
        b.rng = random.Random(7)
        outcomes=[]
        for m in (a,b):
            last=0
            results=[]
            for _ in range(100000):
                m.update(1/60)
                if m.shots != last:
                    results.append(m.made)
                    last=m.shots
                if last==12:
                    break
            self.assertEqual(len(results),12)
            self.assertTrue(any(results) and not all(results))
            outcomes.append(results)
        self.assertNotEqual(*outcomes)
        a.reset()
        self.assertEqual(a.shots,0)
        self.assertEqual(b.shots,12)

    def test_projectile_continuity_and_descending_rim_crossing(self):
        p=Projectile.toward((50,950),(900,850),1,0)
        self.assertEqual(p.position(0),(50,950))
        self.assertAlmostEqual(p.position(p.duration)[0],900)
        self.assertAlmostEqual(p.position(p.duration)[1],850)
        self.assertGreater(p.velocity(p.duration)[1],0)
        for i in range(1,101):
            x,y=p.position(i*p.duration/100)
            prev=p.position((i-1)*p.duration/100)
            self.assertLess(math.dist((x,y),prev),25)

    def test_config_validation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'config.json'
            for data in ['{"fps":60}', '{"shot_make_probability":2}', '{"laps_before_shot":0}', '{"scale":0}', '{"move_speed":NaN}', '{"sprite_canvas":[0,256]}']:
                path.write_text(data)
                with self.assertRaises(ValueError): Config.load(path)

if __name__=='__main__': unittest.main()
