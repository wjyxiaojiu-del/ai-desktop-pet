"""桌面宠物核心 — 纯 QPainter 手绘，零外部素材"""

import math
import random
from PySide6.QtWidgets import QWidget, QApplication, QMenu
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QBrush, QPen, QFont,
    QCursor, QMouseEvent, QPaintEvent
)


class DesktopPet(QWidget):
    """轻量桌面宠物 — 置顶悬浮，可拖拽，纯手绘"""

    PET_SIZE = 140

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedSize(self.PET_SIZE, self.PET_SIZE)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.PET_SIZE - 30,
                      geo.bottom() - self.PET_SIZE - 80)

        self._idle_phase = 0.0
        self._blink_timer = 0
        self._is_blinking = False
        self._blink_progress = 0.0
        self._bounce_offset = 0.0
        self._bounce_velocity = 0.0
        self._action_text = ""
        self._action_text_timer = 0

        self._dragging = False
        self._drag_pos = QPoint()

        self._mood = "normal"
        self._mood_timer = 0

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(16)

        self._blink_reset()
        self.show()

    def _tick(self):
        dt = 16 / 1000.0
        self._idle_phase += dt * 1.8

        if self._bounce_offset > 0.01 or self._bounce_velocity != 0:
            self._bounce_velocity -= 980 * dt * 1.5
            self._bounce_offset += self._bounce_velocity * dt
            if self._bounce_offset <= 0:
                self._bounce_offset = 0
                self._bounce_velocity = 0
        else:
            self._bounce_offset = 0

        self._blink_timer -= 1
        if self._blink_timer <= 0:
            if not self._is_blinking:
                self._is_blinking = True
                self._blink_progress = 0.0

        if self._is_blinking:
            self._blink_progress += dt * 12
            if self._blink_progress >= 2.0:
                self._is_blinking = False
                self._blink_progress = 0.0
                self._blink_reset()

        if self._mood_timer > 0:
            self._mood_timer -= 1
            if self._mood_timer <= 0:
                self._mood = "normal"

        if self._action_text_timer > 0:
            self._action_text_timer -= 1
            if self._action_text_timer <= 0:
                self._action_text = ""

        if random.random() < 0.0008:
            self._jump()

        self.update()

    def _blink_reset(self):
        self._blink_timer = random.randint(60, 200)

    def _jump(self):
        if self._bounce_offset == 0:
            self._bounce_velocity = -180

    def _bounce(self):
        self._bounce_velocity = -120

    def _show_action(self, text: str, duration: int = 80):
        self._action_text = text
        self._action_text_timer = duration

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        float_y = math.sin(self._idle_phase) * 4 - self._bounce_offset
        cx = self.PET_SIZE / 2
        cy = self.PET_SIZE / 2 + float_y

        self._draw_pet(p, cx, cy)

        if self._action_text:
            p.setFont(QFont("Microsoft YaHei", 18))
            p.setPen(QColor(255, 80, 80))
            p.drawText(QRectF(0, cy - 90, self.PET_SIZE, 40),
                       Qt.AlignmentFlag.AlignCenter, self._action_text)

        p.end()

    def _draw_pet(self, p: QPainter, cx: float, cy: float):
        body_r = 48
        body_color = QColor(255, 220, 180)

        path = QPainterPath()
        path.addEllipse(QPoint(cx, cy), body_r, body_r)
        p.fillPath(path, QBrush(body_color))
        p.setPen(QPen(QColor(210, 170, 130), 2))
        p.drawPath(path)

        ear_color = QColor(255, 200, 150)
        self._draw_ear(p, cx - 28, cy - 42, -15, ear_color)
        self._draw_ear(p, cx + 28, cy - 42, 15, ear_color)

        blush = QColor(255, 160, 140, 120)
        p.setBrush(QBrush(blush))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(cx - 30, cy + 8), 10, 6)
        p.drawEllipse(QPoint(cx + 30, cy + 8), 10, 6)

        eye_y = cy - 10
        eye_spacing = 16
        eye_r = 12
        pupil_r = 5
        white = QColor(255, 255, 255)
        dark = QColor(40, 40, 40)

        eye_scale_y = 1.0
        if self._is_blinking:
            if self._blink_progress < 1.0:
                eye_scale_y = 1.0 - self._blink_progress
            else:
                eye_scale_y = self._blink_progress - 1.0

        for side in [-1, 1]:
            ex = cx + side * eye_spacing
            p.save()
            p.translate(ex, eye_y)
            p.scale(1, eye_scale_y)
            p.setBrush(QBrush(white))
            p.setPen(QPen(dark, 1.5))
            p.drawEllipse(QPoint(), eye_r, eye_r)
            if eye_scale_y > 0.1:
                p.setBrush(QBrush(dark))
                p.setPen(Qt.PenStyle.NoPen)
                px = side * 2
                py = -2 + math.sin(self._idle_phase * 1.3) * 1
                p.drawEllipse(QPoint(px, py), pupil_r, pupil_r)
                p.setBrush(QBrush(QColor(255, 255, 255)))
                p.drawEllipse(QPoint(px - 2, py - 3), 2, 2)
            p.restore()

        mouth_y = cy + 16
        if self._mood == "happy":
            self._draw_happy_mouth(p, cx, mouth_y)
        elif self._mood == "surprised":
            self._draw_surprised_mouth(p, cx, mouth_y)
        elif self._mood == "sleepy":
            self._draw_sleepy_mouth(p, cx, mouth_y)
        else:
            self._draw_normal_mouth(p, cx, mouth_y)

    def _draw_ear(self, p: QPainter, x: float, y: float, tilt: float, color: QColor):
        path = QPainterPath()
        path.moveTo(x, y)
        path.quadTo(x + tilt, y - 20, x + tilt * 1.5, y - 28)
        path.quadTo(x + tilt * 0.5, y - 10, x, y)
        p.fillPath(path, QBrush(color))
        p.setPen(QPen(QColor(210, 170, 130), 1.5))
        p.drawPath(path)

    def _draw_normal_mouth(self, p: QPainter, cx: float, y: float):
        p.setPen(QPen(QColor(80, 60, 50), 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(cx - 6, y)
        path.quadTo(cx, y + 5, cx + 6, y)
        p.drawPath(path)

    def _draw_happy_mouth(self, p: QPainter, cx: float, y: float):
        p.setPen(QPen(QColor(80, 60, 50), 2))
        p.setBrush(QBrush(QColor(255, 120, 100, 80)))
        path = QPainterPath()
        path.moveTo(cx - 10, y - 2)
        path.quadTo(cx, y + 8, cx + 10, y - 2)
        p.drawPath(path)

    def _draw_surprised_mouth(self, p: QPainter, cx: float, y: float):
        p.setPen(QPen(QColor(80, 60, 50), 1.8))
        p.setBrush(QBrush(QColor(60, 40, 30, 60)))
        p.drawEllipse(QPoint(cx, y + 2), 7, 7)

    def _draw_sleepy_mouth(self, p: QPainter, cx: float, y: float):
        p.setPen(QPen(QColor(80, 60, 50), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(cx - 5, y + 2)
        path.quadTo(cx, y - 2, cx + 5, y + 2)
        p.drawPath(path)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._mood = "surprised"
            self._mood_timer = 40
            self._bounce()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._mood = "happy"
            self._mood_timer = 60
            self._show_action("❤", 80)
            self._bounce()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._jump()
            self._mood = "happy"
            self._mood_timer = 80
            self._show_action("✨", 80)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setFont(QFont("Microsoft YaHei", 10))
        menu.addAction("😊 摸摸").triggered.connect(lambda: self._on_click_action("摸摸"))
        menu.addAction("🦘 弹跳").triggered.connect(lambda: self._on_click_action("弹跳"))
        menu.addAction("😴 打盹").triggered.connect(lambda: self._on_click_action("打盹"))
        menu.addSeparator()
        menu.addAction("退出").triggered.connect(QApplication.instance().quit)
        menu.exec(QCursor.pos())

    def _on_click_action(self, action: str):
        if action == "摸摸":
            self._mood = "happy"
            self._mood_timer = 100
            self._show_action("❤", 100)
            self._bounce()
        elif action == "弹跳":
            self._jump()
            self._show_action("🦘", 60)
        elif action == "打盹":
            self._mood = "sleepy"
            self._mood_timer = 300
            self._show_action("💤", 300)
