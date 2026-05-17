import os
from dotenv import load_dotenv

load_dotenv()

# LLM 配置
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")

# Home Assistant 配置
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

# 语音配置
TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")

# 窗口配置
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 500
PET_SIZE = 200
