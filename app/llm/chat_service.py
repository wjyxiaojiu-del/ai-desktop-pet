import sys
import os
import re
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from openai import OpenAI
import config


class ChatService:
    def __init__(self):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
        )
        self.model = config.LLM_MODEL
        self.history: list[dict] = []
        self.vision_context: str = ""
        self.system_prompt = (
            "你是一个可爱的桌面宠物助手，名叫'小九'。"
            "你性格活泼、温暖，喜欢用简短有趣的语气回复。"
            "回复尽量控制在 2-3 句话以内，除非用户要求详细解释。"
        )
        self._retriever = None
        self._ha = None

    @property
    def retriever(self):
        if self._retriever is None:
            try:
                from app.rag.retriever import Retriever
                self._retriever = Retriever()
            except Exception:
                self._retriever = None
        return self._retriever

    @property
    def ha(self):
        if self._ha is None:
            try:
                from app.tools.home_assistant import HomeAssistantClient
                self._ha = HomeAssistantClient()
            except Exception:
                self._ha = None
        return self._ha

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        # RAG 检索（懒加载 + 异常保护）
        rag_context = ""
        if self.retriever:
            try:
                rag_context = self.retriever.query(user_message, top_k=3)
            except Exception:
                pass

        messages = [{"role": "system", "content": self._build_system_prompt(rag_context)}]
        messages += self.history

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=512,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"抱歉，我暂时无法回复...({e})"

        # 检查是否需要工具调用
        tool_result = self._try_execute_tool(reply)
        if tool_result:
            self.history.append({"role": "assistant", "content": reply})
            self.history.append({"role": "user", "content": f"[工具调用结果] {tool_result}"})
            try:
                response2 = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages + [
                        {"role": "assistant", "content": reply},
                        {"role": "user", "content": f"工具执行结果：{tool_result}，请用自然语言告诉用户。"}
                    ],
                    max_tokens=256,
                    temperature=0.7,
                )
                reply = response2.choices[0].message.content.strip()
            except Exception:
                reply = f"已执行：{tool_result}"
        else:
            self.history.append({"role": "assistant", "content": reply})

        return reply

    def _build_system_prompt(self, rag_context: str) -> str:
        prompt = self.system_prompt
        if rag_context:
            prompt += f"\n\n【知识库参考】\n{rag_context}"
        if self.vision_context:
            prompt += f"\n\n【当前视觉感知】{self.vision_context}"
        if self.ha and getattr(self.ha, "is_configured", False):
            from app.tools.home_assistant import HA_TOOLS_DESC
            prompt += f"\n\n{HA_TOOLS_DESC}"
        return prompt

    def _try_execute_tool(self, reply: str) -> str:
        if not self.ha or not getattr(self.ha, "is_configured", False):
            return ""

        match = re.search(r"```tool_call\s*(.*?)\s*```", reply, re.DOTALL)
        if not match:
            return ""

        try:
            call = json.loads(match.group(1).strip())
            tool_name = call.get("tool")
            params = call.get("params", {})

            if tool_name == "turn_on":
                result = self.ha.turn_on(params["entity_id"])
            elif tool_name == "turn_off":
                result = self.ha.turn_off(params["entity_id"])
            elif tool_name == "set_light_brightness":
                result = self.ha.set_light_brightness(params["entity_id"], params["brightness"])
            elif tool_name == "get_device_state":
                result = self.ha.get_device_state(params["entity_id"])
            else:
                result = {"error": "未知工具"}

            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"工具调用失败：{e}"

    def clear_history(self):
        self.history.clear()
