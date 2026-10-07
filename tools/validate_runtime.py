"""Run actual Qt windows/timers through both complete outcomes; save visual evidence."""
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PySide6.QtCore import QTimer, QRect, QPoint
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication
from src.assets import Assets
from src.config import Config, PROJECT_ROOT
from src.monitor_controller import MonitorController
from src.state_machine import State

app=QApplication([])
app.setQuitOnLastWindowClosed(False)
root=PROJECT_ROOT/'artifacts'
root.mkdir(exist_ok=True)
cfg=Config(move_speed=1500,patrol_width=180)
assets=Assets(cfg)
controllers=[MonitorController(app.primaryScreen(),replace(cfg,shot_make_probability=p),assets) for p in (1,0)]
seen=[set(),set()]
images=[]


def capture(c, label):
    area=c.area
    # Crop activity only. Composite the actual widget rendering onto a dark desktop.
    left=max(area.left,c.layout.start_x-c.layout.pet_width)
    top=max(area.top,area.floor-360*c.layout.scale)
    width=int(area.right-left)
    height=int(area.floor-top)
    image=QImage(width,height,QImage.Format.Format_ARGB32)
    image.fill(QColor('#1e293b'))
    painter=QPainter(image)
    for window in c.windows:
        window.render(painter,QPoint(round(window.x()-left),round(window.y()-top)))
    painter.setPen(QColor('#dfe7f2'))
    painter.drawText(10,22,label)
    painter.end()
    return image


def observe():
    for i,c in enumerate(controllers):
        state=c.machine.state
        seen[i].add(state.value)
        frame_states=(State.WALK_TO_HOOP,State.SHOOT_PREP,State.BALL_IN_FLIGHT,State.REACTION_SUCCESS,State.REACTION_MISS,State.PICKUP_BALL,State.RETURN_TO_START)
        ready = (state != State.PICKUP_BALL or 0.4 <= c.machine.elapsed <= 0.6) and (state != State.BALL_IN_FLIGHT or c.machine.elapsed >= c.machine.projectile.duration * 0.5) and (state != State.SHOOT_PREP or c.machine.elapsed >= 0.35)
        if ready and state in frame_states and (i,state) not in captured:
            captured.add((i,state))
            images.append(capture(c,('MADE' if i==0 else 'MISS')+' / '+state.value))
    if all(c.machine.completed_cycles>=2 for c in controllers):
        finish(True)


def finish(success):
    observer.stop()
    timeout.stop()
    summary=[]
    for i,c in enumerate(controllers):
        summary.append({'outcome':'made' if i==0 else 'miss','cycles':c.machine.completed_cycles,'shots':c.machine.shots,'shot_laps':list(c.machine.shot_laps),'states':sorted(seen[i])})
        c.close()
    if images:
        w=max(im.width() for im in images)
        h=max(im.height() for im in images)
        sheet=QImage(w*2,h*((len(images)+1)//2),QImage.Format.Format_ARGB32)
        sheet.fill(QColor('#101827'))
        painter=QPainter(sheet)
        for i,im in enumerate(images): painter.drawImage((i%2)*w,(i//2)*h,im)
        painter.end()
        sheet.save(str(root/'runtime-contact-sheet.png'))
    (root/'runtime-validation.json').write_text(json.dumps({'passed':success,'platform':app.platformName(),'monitors':summary},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    app.exit(0 if success else 1)

captured=set()
observer=QTimer()
observer.timeout.connect(observe)
observer.start(15)
timeout=QTimer()
timeout.setSingleShot(True)
timeout.timeout.connect(lambda:finish(False))
timeout.start(24000)
sys.exit(app.exec())
