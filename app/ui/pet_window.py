import sys
import os
import time
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QApplication,
    QFrame, QSizePolicy, QScrollArea, QSpacerItem,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter, QPaintEvent

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.emotion.fsm import EmotionFSM, Emotion
from app.llm.chat_service import ChatService
from app.speech.tts import TTS
from app.speech.asr import ASR
from app.vision.camera import Camera


class ChatWorker(QThread):
    reply_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, chat_service: ChatService, text: str):
        super().__init__()
        self.chat_service = chat_service
        self.text = text

    def run(self):
        try:
            reply = self.chat_service.chat(self.text)
            self.reply_ready.emit(reply)
        except Exception as e:
            self.error_occurred.emit(str(e))


class TTSWorker(QThread):
    finished = Signal()

    def __init__(self, tts: TTS, text: str):
        super().__init__()
        self.tts = tts
        self.text = text

    def run(self):
        try:
            self.tts.speak(self.text)
        except Exception:
            pass
        self.finished.emit()


class BubbleLabel(QLabel):
    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setFont(QFont("Microsoft YaHei", 11))
        self.setContentsMargins(14, 10, 14, 10)
        self.setMaximumWidth(340)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        if is_user:
            self.setStyleSheet(
                "QLabel {"
                "  background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #95EC69, stop:1 #7AD853);"
                "  border-radius: 16px;"
                "  color: #000;"
                "}"
            )
            self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFFFFF;"
                "  border-radius: 16px;"
                "  color: #000;"
                "  border: 1px solid #E8E8E8;"
                "}"
            )
            self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.setText(text)
        self.adjustSize()


class PetFrame(QFrame):
    """带渐变背景的宠物展示区"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(220)
        self.setFrameShape(QFrame.Shape.NoFrame)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#E0F7FA"))
        gradient.setColorAt(1, QColor("#B2EBF2"))
        painter.fillRect(self.rect(), QBrush(gradient))
        super().paintEvent(event)


class PetWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 桌面宠物 - 小九")
        self.setMinimumSize(460, 680)
        self.resize(480, 720)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

        self.emotion_fsm = EmotionFSM()
        self.chat_service = ChatService()
        self.tts = TTS()
        self.asr = ASR()
        self.camera = Camera()
        self._is_typing = False
        self._is_recording = False
        self._last_face_time = time.time()
        self._face_greeted = False
        self._worker: Optional[ChatWorker] = None
        self._tts_worker: Optional[TTSWorker] = None
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._do_blink)
        self._blink_timer.start(3500)
        self._breath_timer = QTimer(self)
        self._breath_timer.timeout.connect(self._do_breath)
        self._breath_timer.start(2000)
        self._vision_timer = QTimer(self)
        self._vision_timer.timeout.connect(self._on_vision_tick)
        self._vision_timer.start(3000)
        self._anim_jumping = False
        self._anim_shaking = False

        self._build_ui()
        self._connect_signals()
        self._init_camera()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== 宠物展示区 =====
        self.pet_container = PetFrame()
        pet_layout = QVBoxLayout(self.pet_container)
        pet_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pet_layout.setSpacing(4)

        self.pet_label = QLabel("🐱")
        self.pet_label.setFont(QFont("Segoe UI Emoji", 90))
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_label.setFixedSize(140, 140)
        pet_layout.addWidget(self.pet_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.emotion_label = QLabel("neutral")
        self.emotion_label.setFont(QFont("Microsoft YaHei", 11))
        self.emotion_label.setStyleSheet("color: #00695C;")
        self.emotion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pet_layout.addWidget(self.emotion_label)

        layout.addWidget(self.pet_container)

        # ===== 聊天记录区（带滚动） =====
        self.chat_area = QFrame()
        self.chat_area.setStyleSheet("QFrame { background: #F5F5F5; }")
        chat_layout = QVBoxLayout(self.chat_area)
        chat_layout.setContentsMargins(12, 12, 12, 12)
        chat_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.chat_scroll_contents = QWidget()
        self.chat_scroll_layout = QVBoxLayout(self.chat_scroll_contents)
        self.chat_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_scroll_layout.setSpacing(10)
        self.chat_scroll_layout.addStretch()
        self.scroll_area.setWidget(self.chat_scroll_contents)

        chat_layout.addWidget(self.scroll_area)
        layout.addWidget(self.chat_area, stretch=1)

        # ===== 输入区 =====
        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background: #FFFFFF; border-top: 1px solid #E0E0E0; }")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)

        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.setFixedSize(42, 42)
        self.mic_btn.setFont(QFont("Segoe UI Emoji", 14))
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setToolTip("按住说话")
        self.mic_btn.setStyleSheet(self._mic_btn_style("#FF6B6B"))
        input_layout.addWidget(self.mic_btn)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("和小九说点什么吧...")
        self.input_box.setFont(QFont("Microsoft YaHei", 12))
        self.input_box.setFixedHeight(42)
        self.input_box.setStyleSheet(
            "QLineEdit {"
            "  border: 1px solid #DDD;"
            "  border-radius: 21px;"
            "  padding: 4px 16px;"
            "  background: #F8F8F8;"
            "}"
            "QLineEdit:focus {"
            "  border: 2px solid #4ECDC4;"
            "  background: #FFFFFF;"
            "}"
        )
        input_layout.addWidget(self.input_box, stretch=1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(64, 42)
        self.send_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(
            "QPushButton {"
            "  border: none;"
            "  border-radius: 21px;"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4ECDC4, stop:1 #44A08D);"
            "  color: white;"
            "}"
            "QPushButton:hover {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #44A08D, stop:1 #3D8B7A);"
            "}"
            "QPushButton:pressed {"
            "  background: #3D8B7A;"
            "}"
        )
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

        # ===== 状态栏 =====
        self.status_label = QLabel("  就绪")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setStyleSheet(
            "QLabel { color: #666; background: #FAFAFA; padding: 6px 12px; border-top: 1px solid #EEE; }"
        )
        layout.addWidget(self.status_label)

    def _mic_btn_style(self, color: str) -> str:
        return (
            f"QPushButton {{"
            f"  border: none;"
            f"  border-radius: 21px;"
            f"  background: {color};"
            f"  color: white;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {color};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: #E74C3C;"
            f"}}"
        )

    def _connect_signals(self):
        self.send_btn.clicked.connect(self._on_send)
        self.input_box.returnPressed.connect(self._on_send)
        self.emotion_fsm.on_change(self._on_emotion_change)
        self.mic_btn.pressed.connect(self._on_mic_pressed)
        self.mic_btn.released.connect(self._on_mic_released)
        # API 超时计时器 (30秒)
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_chat_timeout)
        self._chat_start_time = 0.0

    def _init_camera(self):
        try:
            ok = self.camera.start()
            if ok:
                self.camera.on_face_change(self._on_face_change)
                self._set_status("摄像头已启动")
            else:
                self._set_status("摄像头不可用")
        except Exception as e:
            self._set_status(f"摄像头初始化失败: {e}")

    def _set_status(self, text: str):
        self.status_label.setText(f"  {text}")

    def _on_face_change(self, count: int):
        if count > 0:
            self._last_face_time = time.time()
            if not self._face_greeted:
                self._face_greeted = True
                self.emotion_fsm.set_emotion(Emotion.HAPPY)
                self._animate_jump()
                self._add_bubble("[小九看到你啦！]", is_user=False)
                self._set_status("检测到用户")
        else:
            self._face_greeted = False

    def _on_vision_tick(self):
        try:
            summary = self.camera.get_detection_summary()
            self.chat_service.vision_context = summary
            if time.time() - self._last_face_time > 10 and self.camera.face_count == 0:
                if self.emotion_fsm.current != Emotion.SLEEPY:
                    self.emotion_fsm.set_emotion(Emotion.SLEEPY)
                    self._set_status("小九在打瞌睡...")
        except Exception:
            pass

    def _add_bubble(self, text: str, is_user: bool = False):
        bubble = BubbleLabel(text, is_user)
        hbox = QHBoxLayout()
        if is_user:
            hbox.addStretch()
            hbox.addWidget(bubble)
        else:
            hbox.addWidget(bubble)
            hbox.addStretch()
        # 插入到 stretch 之前
        self.chat_scroll_layout.insertLayout(self.chat_scroll_layout.count() - 1, hbox)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_send(self, text: str = ""):
        if not text:
            text = self.input_box.text().strip()
        if not text:
            return
        self.input_box.clear()
        self._add_bubble(text, is_user=True)

        self.emotion_fsm.update_from_text(text)

        # 禁用按钮防止重复发送
        self.send_btn.setEnabled(False)
        self.input_box.setEnabled(False)
        self._chat_start_time = time.time()
        self._set_status("正在连接 API...")
        self._is_typing = True
        self._update_pet_emoji()
        self._animate_thinking()

        # 启动超时计时器 (30秒)
        self._timeout_timer.start(30000)

        # 清理旧线程
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)

        self._worker = ChatWorker(self.chat_service, text)
        self._worker.reply_ready.connect(self._on_reply_ready)
        self._worker.error_occurred.connect(self._on_chat_error)
        self._worker.start()

    def _on_reply_ready(self, reply: str):
        self._timeout_timer.stop()
        elapsed = time.time() - self._chat_start_time
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)

        self._add_bubble(reply, is_user=False)
        self.emotion_fsm.update_from_text(reply)
        self._set_status(f"就绪 (耗时 {elapsed:.1f}s)")
        self._is_typing = False
        self._update_pet_emoji()
        self._animate_reply()

        # 语音播报（后台线程，不阻塞 UI）
        if self._tts_worker and self._tts_worker.isRunning():
            self._tts_worker.terminate()
            self._tts_worker.wait(1000)
        self._tts_worker = TTSWorker(self.tts, reply)
        self._tts_worker.start()

    def _on_chat_error(self, error: str):
        self._timeout_timer.stop()
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)
        self._is_typing = False
        self._update_pet_emoji()
        self._add_bubble(f"[错误] {error}", is_user=False)
        self._set_status("请求失败")

    def _on_chat_timeout(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)
        self._is_typing = False
        self._update_pet_emoji()
        self._add_bubble("[超时] API 响应超过 30 秒，请检查网络或模型是否可用", is_user=False)
        self._set_status("请求超时")

    def _on_mic_pressed(self):
        if self._is_recording:
            return
        self._is_recording = True
        self.mic_btn.setStyleSheet(self._mic_btn_style("#E74C3C"))
        self._set_status("正在录音... 松开发送")
        try:
            self.asr.record_start()
        except Exception as e:
            self._set_status(f"录音失败: {e}")
            self._is_recording = False
            self.mic_btn.setStyleSheet(self._mic_btn_style("#FF6B6B"))

    def _on_mic_released(self):
        if not self._is_recording:
            return
        self._is_recording = False
        self.mic_btn.setStyleSheet(self._mic_btn_style("#FF6B6B"))
        self._set_status("识别中...")
        try:
            text = self.asr.record_stop()
            if text:
                self.input_box.setText(text)
                self._on_send(text)
            else:
                self._set_status("没有听清，请再说一遍")
        except Exception as e:
            self._set_status(f"识别失败: {e}")

    def _on_emotion_change(self, emotion: Emotion):
        self.emotion_label.setText(emotion.value)
        self._update_pet_emoji()
        if emotion == Emotion.HAPPY:
            self._animate_jump()
        elif emotion == Emotion.SAD:
            self._animate_shake()
        elif emotion == Emotion.ANGRY:
            self._animate_shake(intensity=8)
        elif emotion == Emotion.SLEEPY:
            self._animate_breath_slow()

    def _update_pet_emoji(self):
        if self._is_typing:
            self.pet_label.setText("🤔")
            return
        emoji_map = {
            Emotion.NEUTRAL: "🐱",
            Emotion.HAPPY: "😸",
            Emotion.SAD: "😿",
            Emotion.ANGRY: "😾",
            Emotion.SLEEPY: "😴",
        }
        self.pet_label.setText(emoji_map.get(self.emotion_fsm.current, "🐱"))

    # ===== 动画方法 =====

    def _animate_jump(self):
        if self._anim_jumping:
            return
        self._anim_jumping = True
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(400)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.5, QPoint(start.x(), start.y() - 30))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.OutInQuad)
        anim.finished.connect(lambda: setattr(self, "_anim_jumping", False))
        anim.start()

    def _animate_shake(self, intensity: int = 5):
        if self._anim_shaking:
            return
        self._anim_shaking = True
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(300)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.2, QPoint(start.x() - intensity, start.y()))
        anim.setKeyValueAt(0.4, QPoint(start.x() + intensity, start.y()))
        anim.setKeyValueAt(0.6, QPoint(start.x() - intensity, start.y()))
        anim.setKeyValueAt(0.8, QPoint(start.x() + intensity, start.y()))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.Linear)
        anim.finished.connect(lambda: setattr(self, "_anim_shaking", False))
        anim.start()

    def _animate_thinking(self):
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(600)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.5, QPoint(start.x(), start.y() - 10))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()

    def _animate_reply(self):
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(300)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.5, QPoint(start.x(), start.y() - 15))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()

    def _do_blink(self):
        if self._is_typing or self._anim_jumping or self._anim_shaking:
            return
        if self.emotion_fsm.current == Emotion.SLEEPY:
            return
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(200)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.5, QPoint(start.x(), start.y() + 5))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()

    def _do_breath(self):
        if self._is_typing or self._anim_jumping or self._anim_shaking:
            return
        if self.emotion_fsm.current == Emotion.SLEEPY:
            return
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(1000)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.5, QPoint(start.x(), start.y() - 3))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.start()

    def _animate_breath_slow(self):
        anim = QPropertyAnimation(self.pet_label, b"pos", self)
        start = self.pet_label.pos()
        anim.setDuration(2000)
        anim.setKeyValueAt(0, start)
        anim.setKeyValueAt(0.5, QPoint(start.x(), start.y() - 5))
        anim.setKeyValueAt(1, start)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.start()

    def closeEvent(self, event):
        try:
            self.camera.stop()
        except Exception:
            pass
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(1000)
        if self._tts_worker and self._tts_worker.isRunning():
            self._tts_worker.terminate()
            self._tts_worker.wait(1000)
        event.accept()
