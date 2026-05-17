import cv2
import threading
import time
from typing import Callable, Optional


class Camera:
    def __init__(self, device_id: int = 0):
        self._cap: Optional[cv2.VideoCapture] = None
        self._device_id = device_id
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame = None
        self._face_count = 0
        self._lock = threading.Lock()
        self._callbacks: list[Callable] = []
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def start(self):
        self._cap = cv2.VideoCapture(self._device_id)
        if not self._cap.isOpened():
            print("[Camera] 无法打开摄像头")
            return False
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def _loop(self):
        while self._running and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._frame = frame
                # 每帧都做轻量人脸检测
                self._detect_faces(frame)

    def _detect_faces(self, frame):
        try:
            small = cv2.resize(frame, (0, 0), fx=0.3, fy=0.3)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, 1.1, 3)
            new_count = len(faces)
            if new_count != self._face_count:
                self._face_count = new_count
                for cb in self._callbacks:
                    cb(self._face_count)
        except Exception:
            pass

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        if self._cap:
            self._cap.release()

    def get_frame(self):
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def on_face_change(self, callback: Callable):
        self._callbacks.append(callback)

    @property
    def face_count(self) -> int:
        return self._face_count

    def get_detection_summary(self) -> str:
        if self._face_count > 0:
            return f"检测到 {self._face_count} 张人脸，用户正在屏幕前。"
        return "未检测到人脸，用户可能不在屏幕前。"
