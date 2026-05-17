from enum import Enum


class Emotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SLEEPY = "sleepy"


# 关键词 -> 情绪映射
_EMOTION_KEYWORDS = {
    Emotion.HAPPY: ["开心", "高兴", "太好了", "哈哈", "嘿嘿", "不错", "棒", "赞", "喜欢", "爱", "谢谢"],
    Emotion.SAD: ["难过", "伤心", "不开心", "唉", "呜呜", "累了", "烦", "无聊", "孤独"],
    Emotion.ANGRY: ["生气", "愤怒", "讨厌", "烦死了", "气死", "混蛋", "该死"],
    Emotion.SLEEPY: ["困", "睡觉", "晚安", "休息", "累了", "打盹"],
}


class EmotionFSM:
    def __init__(self):
        self.current = Emotion.NEUTRAL
        self._listeners: list = []

    def on_change(self, callback):
        self._listeners.append(callback)

    def set_emotion(self, emotion: Emotion):
        if emotion != self.current:
            self.current = emotion
            for cb in self._listeners:
                cb(emotion)

    def analyze_text(self, text: str) -> Emotion:
        text_lower = text.lower()
        for emotion, keywords in _EMOTION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return emotion
        return Emotion.NEUTRAL

    def update_from_text(self, text: str):
        emotion = self.analyze_text(text)
        self.set_emotion(emotion)

    def reset(self):
        self.set_emotion(Emotion.NEUTRAL)
