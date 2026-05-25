> **中文** | [English](README_en.md)

# AI 多模态桌面宠物智能家居助手

一个基于 Python、PySide6、LangChain、OpenCV 和本地大模型的多模态智能桌面宠物，支持文本、语音、图像三模态自然交互，可接入 Home Assistant 控制智能家居设备。

---

## 功能特性

- **桌面宠物 UI**：PySide6 实现的常驻桌面窗口，Emoji 表情 + QPropertyAnimation 动画系统
- **本地大模型对话**：支持任意 OpenAI 兼容 API（Ollama、vLLM、OpenAI 等）
- **语音交互**：faster-whisper 语音识别 + pyttsx3/edge-tts 语音合成，按住麦克风说话
- **视觉感知**：OpenCV 摄像头采集 + 人脸检测，无人时自动打瞌睡，有人时主动打招呼
- **情感 FSM**：5 种情绪状态（neutral/happy/sad/angry/sleepy）+ 10+ 种动画动作
- **RAG 知识库**：LangChain + Chroma 向量检索，支持本地 Markdown 文档
- **Agent 工具调用**：LLM 自动判断意图，调用 Home Assistant API 控制设备
- **通用实体控制器**：通过 entity_id 自动路由，理论上支持所有 HA 已接入设备

---

## 技术架构

```
app/
  main.py              # 入口
  ui/
    pet_window.py      # 桌面宠物窗口 + 动画 + 对话面板
  llm/
    chat_service.py    # OpenAI 兼容 API + RAG + 工具调用
  emotion/
    fsm.py             # 有限状态机情感系统
  vision/
    camera.py          # OpenCV 摄像头 + 人脸检测
  speech/
    asr.py             # faster-whisper 语音识别
    tts.py             # pyttsx3 / edge-tts 语音合成
  rag/
    retriever.py       # Chroma 向量检索
  tools/
    home_assistant.py  # Home Assistant API 封装
```

---

## 安装

```bash
pip install -r requirements.txt
```

### 可选依赖

- **Ollama**（推荐）：本地运行大模型，访问 https://ollama.com 下载
- **Home Assistant**：真实智能家居控制，需配置 `HA_URL` 和 `HA_TOKEN`

---

## 配置

复制 `.env` 并修改：

```env
# LLM 配置
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
LLM_API_KEY=ollama

# Home Assistant (可选)
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your_long_lived_token

# TTS 语音
TTS_VOICE=zh-CN-XiaoxiaoNeural
```

---

## 使用

```bash
python app/main.py
```

### 交互方式

1. **文本输入**：在输入框打字，按回车或点击发送
2. **语音输入**：按住麦克风按钮 🎤 说话，松开后自动识别并发送
3. **视觉感知**：自动检测人脸，有人时宠物会打招呼，无人 10 秒后打瞌睡
4. **智能家居**：说出指令如"打开客厅灯"，LLM 会自动调用 Home Assistant

---

## 演示场景

### 1. 自然聊天
用户："我今天有点累。"  
宠物：进入关心状态，语音安慰回复。

### 2. 视觉感知
用户坐到电脑前。  
宠物：检测到人脸，主动打招呼 + 跳跃动画。

### 3. 智能家居控制
用户："有点暗，帮我把客厅灯调亮。"  
系统：理解意图 → 调用 Home Assistant → 调整灯光 → 语音反馈。

---

## 项目结构

```
ai-desktop-pet/
  app/
    main.py
    ui/          pet_window.py
    llm/         chat_service.py
    emotion/     fsm.py
    vision/      camera.py
    speech/      asr.py, tts.py
    rag/         retriever.py
    tools/       home_assistant.py
  docs/
    home_devices.md
    user_profile.md
    pet_personality.md
  config.py
  .env
  requirements.txt
```

---

## 简历亮点

> **AI 多模态桌面宠物智能家居助手**  
> 基于 Python、PySide6、LangChain、OpenCV、Qwen2/Llama3 和 Home Assistant API 实现本地离线多模态智能助手，支持文本、语音、图像三模态自然交互。设计有限状态机情感系统，实现 5 种情绪状态与 10+ 种表情动作；集成 RAG 检索增强与 Agent 工具调用能力，通过通用 Home Assistant 实体控制器支持灯光、空调、窗帘等 100+ 智能家居设备控制；支持本地运行与隐私保护。

---

## License

MIT
