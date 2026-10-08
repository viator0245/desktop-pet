"""Original generic placeholder player, deliberately not a licensed character sprite."""
import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

STATES = ("idle", "walk_dribble", "shoot_prep", "shoot_release", "reaction_success", "reaction_miss", "pickup_ball")


def hand_anchor(state, phase):
    if state == "shoot_prep":
        return (177 - 2*phase, 159 - 64*phase)
    if state == "shoot_release":
        return (175 + 10*phase, 95 - 53*phase)
    if state == "pickup_ball":
        # bend down then stand up; ball attaches exactly at deepest bend
        bend = math.sin(math.pi * phase)
        return (177, 160 + 82 * bend)
    return (177, 159)


def draw_placeholder(p, state, phase):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink = QColor("#352d3a")
    skin = QColor("#ffcc9d")
    red = QColor("#e54649")
    stride = math.sin(phase * math.tau) if state == "walk_dribble" else 0
    bend = math.sin(math.pi * phase) * 45 if state == "pickup_ball" else 0
    bob = abs(stride)*3
    p.setPen(QPen(ink, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    # Feet remain on the canvas baseline.
    p.setBrush(ink)
    for x in (109-stride*14, 144+stride*14):
        p.drawRoundedRect(QRectF(x-16, 241, 35, 13), 5, 5)
    p.setBrush(skin)
    p.drawRoundedRect(QRectF(102-stride*14, 199, 15, 43), 6, 6)
    p.drawRoundedRect(QRectF(140+stride*14, 199, 15, 43), 6, 6)
    p.setBrush(red.darker(115))
    p.drawRoundedRect(QRectF(94, 180+bob, 68, 31), 6, 6)
    # Torso and head lower visibly during pickup.
    p.setBrush(red)
    path = QPainterPath()
    path.moveTo(105, 115+bend+bob)
    path.lineTo(152, 115+bend+bob)
    path.lineTo(165, 185+bend*0.3)
    path.lineTo(92, 185+bend*0.3)
    path.closeSubpath()
    p.drawPath(path)
    p.setPen(QPen(QColor("white"), 3))
    p.drawLine(QPointF(119, 139+bend), QPointF(119, 168+bend))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(130, 139+bend, 15, 29), 5, 5)
    p.setPen(QPen(ink, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    # Arms: prep, extension, follow-through, fist pump and low pickup.
    hx, hy = hand_anchor(state, phase)
    if state == "reaction_success":
        hx, hy = 178, 77 - 12*math.sin(phase*math.tau)
    elbow = (170, 125+bend) if state not in ("shoot_prep", "shoot_release", "reaction_success") else (175, 95)
    p.setPen(QPen(skin, 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(151, 125+bend), QPointF(*elbow))
    p.drawLine(QPointF(*elbow), QPointF(hx, hy))
    p.drawLine(QPointF(105, 127+bend), QPointF(85, 169+bend*0.5))
    p.setPen(QPen(ink, 3))
    p.setBrush(skin)
    p.drawEllipse(QPointF(hx, hy), 8, 8)
    p.drawEllipse(QRectF(97, 55+bend+bob, 65, 64))
    # Red hair, a simple generic short haircut.
    p.setBrush(QColor("#b72836"))
    hair = QPainterPath()
    hair.moveTo(97, 82+bend+bob)
    for x, y in [(100,58),(111,48),(119,56),(128,45),(137,54),(151,50),(163,66),(160,82),(147,72),(112,73)]:
        hair.lineTo(x, y+bend+bob)
    hair.closeSubpath()
    p.drawPath(hair)
    p.setBrush(QColor("white"))
    if state == "reaction_miss":
        p.drawEllipse(QRectF(115, 81+bend, 13, 17))
        p.drawEllipse(QRectF(142, 81+bend, 13, 17))
        p.setBrush(ink)
        p.drawEllipse(QPointF(123,90+bend), 2, 3)
        p.drawEllipse(QPointF(149,90+bend), 2, 3)
        p.drawEllipse(QRectF(132, 101+bend, 11, 13))
        p.setPen(QPen(QColor("#72c6ed"), 4))
        p.drawLine(QPointF(168,81), QPointF(171,93))
    elif state == "reaction_success":
        p.drawArc(QRectF(114, 81, 15, 12), 0, 180*16)
        p.drawArc(QRectF(139, 81, 15, 12), 0, 180*16)
        p.setBrush(QColor("white"))
        p.drawRoundedRect(QRectF(124, 99, 25, 12), 4, 4)
    else:
        p.setBrush(ink)
        p.drawEllipse(QPointF(122, 88+bend+bob), 3, 4)
        p.drawEllipse(QPointF(146, 88+bend+bob), 3, 4)
        p.drawLine(QPointF(130, 105+bend+bob), QPointF(145, 105+bend+bob))
