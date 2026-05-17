"""麦克风 + ASR 诊断脚本"""
import sys
import os
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 50)
print("麦克风 + ASR 诊断")
print("=" * 50)

# 1. 测试 sounddevice
print("\n[1/4] 测试 sounddevice...")
try:
    import sounddevice as sd
    devices = sd.query_devices()
    print(f"  发现 {len(devices)} 个音频设备")
    default_input = sd.query_devices(kind='input')
    print(f"  默认输入设备: {default_input['name']}")
    print(f"  采样率: {default_input['default_samplerate']}Hz")
except Exception as e:
    print(f"  错误: {e}")
    print("  修复: pip install --upgrade sounddevice")

# 2. 测试录音
print("\n[2/4] 测试录音 (3秒)...")
try:
    import numpy as np
    from scipy.io.wavfile import write as wav_write

    duration = 3
    sample_rate = 16000
    print(f"  开始录音，请对着麦克风说话...")

    audio_data = []

    def callback(indata, frames, time_info, status):
        audio_data.append(indata.copy())

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.float32, callback=callback)
    stream.start()
    time.sleep(duration)
    stream.stop()
    stream.close()

    audio = np.concatenate(audio_data, axis=0)
    volume = np.abs(audio).mean()
    print(f"  录音完成，平均音量: {volume:.4f}")

    if volume < 0.01:
        print("  警告: 音量太小，可能没有检测到声音！")
        print("  请检查: 1) 麦克风是否静音 2) 麦克风权限 3) 系统默认输入设备")
    else:
        print("  音量正常")

    # 保存测试音频
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    audio_int16 = np.int16(audio * 32767)
    wav_write(path, sample_rate, audio_int16)
    print(f"  测试音频已保存: {path}")
except Exception as e:
    print(f"  错误: {e}")

# 3. 测试 faster-whisper
print("\n[3/4] 测试 faster-whisper...")
try:
    from faster_whisper import WhisperModel
    print("  加载模型中 (首次会下载，约 150MB)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("  模型加载成功")
except Exception as e:
    print(f"  错误: {e}")

# 4. 测试语音识别
print("\n[4/4] 测试语音识别...")
try:
    if 'path' in dir() and os.path.exists(path):
        segments, info = model.transcribe(path, language="zh", beam_size=5)
        text = "".join([seg.text for seg in segments]).strip()
        print(f"  识别结果: '{text}'")
        if not text:
            print("  警告: 识别结果为空！")
    else:
        print("  跳过: 没有测试音频")
except Exception as e:
    print(f"  错误: {e}")

print("\n" + "=" * 50)
print("诊断完成。把上面的输出贴给我，我帮你排查。")
print("=" * 50)
