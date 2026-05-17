"""全链路诊断: LLM + 麦克风 + TTS"""
import sys, os, time, tempfile

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("全链路诊断")
print("=" * 60)

# ========== 1. LLM 测试 ==========
print("\n[1/4] 测试 LLM 连接...")
try:
    import config
    from openai import OpenAI
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    t0 = time.time()
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=50,
    )
    latency = time.time() - t0
    print(f"  模型: {config.LLM_MODEL}")
    print(f"  延迟: {latency:.2f}s")
    print(f"  回复: {resp.choices[0].message.content[:50]}")
    if latency > 5:
        print("  警告: 延迟超过5秒，模型可能太大或网络慢")
except Exception as e:
    print(f"  错误: {e}")

# ========== 2. 麦克风测试 ==========
print("\n[2/4] 测试麦克风录音...")
try:
    import sounddevice as sd
    import numpy as np
    from scipy.io.wavfile import write as wav_write

    dev = sd.query_devices(kind='input')
    print(f"  默认麦克风: {dev['name']}")

    audio_data = []
    def cb(indata, frames, t, status):
        audio_data.append(indata.copy())

    print("  开始录音3秒，请说话...")
    stream = sd.InputStream(samplerate=16000, channels=1, dtype=np.float32, callback=cb)
    stream.start()
    time.sleep(3)
    stream.stop()
    stream.close()

    audio = np.concatenate(audio_data, axis=0)
    vol = np.abs(audio).mean()
    print(f"  音量: {vol:.4f} (正常应 > 0.01)")
    if vol < 0.01:
        print("  错误: 音量太小，麦克风可能静音或未授权")
    else:
        print("  录音正常")

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav_write(path, 16000, np.int16(audio * 32767))

    print("\n  测试语音识别...")
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(path, language="zh")
    text = "".join([s.text for s in segs]).strip()
    print(f"  识别结果: '{text}'")
    if not text:
        print("  警告: 识别为空")
except Exception as e:
    print(f"  错误: {e}")

# ========== 3. TTS 测试 ==========
print("\n[3/4] 测试 TTS...")
try:
    from app.speech.tts import TTS
    tts = TTS()
    print("  测试 pyttsx3 (离线，声音机器人)...")
    tts.speak("你好，我是小九")
    print("  pyttsx3 播放完成")
except Exception as e:
    print(f"  pyttsx3 错误: {e}")

try:
    import asyncio
    from edge_tts import Communicate
    print("\n  测试 edge-tts (在线，声音更自然)...")
    t0 = time.time()
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    comm = Communicate("你好，我是小九", voice="zh-CN-XiaoxiaoNeural")
    asyncio.run(comm.save(path))
    print(f"  edge-tts 生成完成，耗时 {time.time()-t0:.2f}s")
    print(f"  音频文件: {path}")
    os.startfile(path)
    print("  已播放")
except Exception as e:
    print(f"  edge-tts 错误: {e}")

# ========== 4. 优化建议 ==========
print("\n" + "=" * 60)
print("诊断完成。常见问题:")
print("  - 没回复: 检查 API Key / 模型名 / 网络")
print("  - 听不见: 检查麦克风权限 + 是否静音")
print("  - 延迟高: 换小模型或 edge-tts")
print("  - 声音机器人: 改用 edge-tts (在线，更自然)")
print("=" * 60)
