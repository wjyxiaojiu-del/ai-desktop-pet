"""语音识别 (ASR) - faster-whisper"""

import os
import tempfile
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write


class ASR:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self._sample_rate = 16000
        self._recording = False
        self._audio_data: list[np.ndarray] = []

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            # CPU 模式，自动下载模型到本地缓存
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )

    def record_start(self):
        self._recording = True
        self._audio_data = []
        self._stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype=np.float32,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _audio_callback(self, indata, frames, time_info, status):
        if self._recording:
            self._audio_data.append(indata.copy())

    def record_stop(self) -> str:
        self._recording = False
        self._stream.stop()
        self._stream.close()

        if not self._audio_data:
            return ""

        audio = np.concatenate(self._audio_data, axis=0)
        # 归一化到 int16
        audio_int16 = np.int16(audio * 32767)

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        wav_write(path, self._sample_rate, audio_int16)

        text = self.transcribe(path)
        os.remove(path)
        return text

    def transcribe(self, audio_path: str) -> str:
        self._load_model()
        segments, _ = self._model.transcribe(audio_path, language="zh", beam_size=5)
        text = " ".join([seg.text for seg in segments]).strip()
        return text
