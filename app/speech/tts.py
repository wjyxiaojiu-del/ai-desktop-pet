"""语音合成 (TTS) - edge-tts (在线高质量，默认) + pyttsx3 (离线备用)"""

import os
import tempfile
import asyncio
import pyttsx3
import config


class TTS:
    def __init__(self, voice: str = config.TTS_VOICE, engine: str = "edge"):
        self.voice = voice
        self.engine_type = engine
        self._engine = None
        self._edge_voice = voice

    def _init_pyttsx3(self):
        if self._engine is None:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 180)
            voices = self._engine.getProperty("voices")
            for v in voices:
                if "chinese" in v.name.lower() or "zh" in v.id.lower():
                    self._engine.setProperty("voice", v.id)
                    break

    def speak(self, text: str):
        if not text:
            return
        if self.engine_type == "edge":
            self._speak_edge(text)
        else:
            self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text: str):
        self._init_pyttsx3()
        self._engine.say(text)
        self._engine.runAndWait()

    def _speak_edge(self, text: str):
        """手动处理 asyncio，兼容 QThread"""
        import edge_tts
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            communicate = edge_tts.Communicate(text, voice=self._edge_voice)
            # 手动创建事件循环（避免 QThread 中的冲突）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(communicate.save(path))
            loop.close()
            # Windows 播放 mp3
            os.startfile(path)
        except Exception:
            # edge-tts 失败时回退到 pyttsx3
            self._speak_pyttsx3(text)
