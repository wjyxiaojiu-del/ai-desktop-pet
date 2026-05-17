"""Home Assistant API 通用实体控制器 + Mock 演示模式"""

import json
import urllib.request
from typing import Any
import config


class HomeAssistantClient:
    def __init__(self, url: str = config.HA_URL, token: str = config.HA_TOKEN):
        self.url = url.rstrip("/")
        self.token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._mock = not bool(token)
        self._mock_devices = {
            "light.living_room": {"state": "off", "brightness": 0, "friendly_name": "客厅灯"},
            "light.bedroom": {"state": "off", "brightness": 0, "friendly_name": "卧室灯"},
            "climate.living_room_ac": {"state": "off", "temperature": 26, "friendly_name": "客厅空调"},
            "cover.bedroom_curtain": {"state": "closed", "position": 0, "friendly_name": "卧室窗帘"},
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> Any:
        url = f"{self.url}{endpoint}"
        req = urllib.request.Request(
            url,
            method=method,
            headers=self._headers,
            data=json.dumps(data).encode("utf-8") if data else None,
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def get_states(self) -> list[dict]:
        if self._mock:
            return [
                {"entity_id": k, "state": v["state"], "attributes": {"friendly_name": v["friendly_name"]}}
                for k, v in self._mock_devices.items()
            ]
        return self._request("GET", "/api/states")

    def call_service(self, domain: str, service: str, data: dict) -> dict:
        entity_id = data.get("entity_id", "")
        if self._mock:
            result = self._mock_call(domain, service, entity_id, data)
            print(f"[HA Mock] {domain}/{service} -> {entity_id}: {result}")
            return result
        return self._request("POST", f"/api/services/{domain}/{service}", data)

    def _mock_call(self, domain: str, service: str, entity_id: str, data: dict) -> dict:
        if entity_id not in self._mock_devices:
            return {"error": f"设备 {entity_id} 不存在"}
        dev = self._mock_devices[entity_id]
        if service == "turn_on":
            dev["state"] = "on"
            return {"entity_id": entity_id, "state": "on", "mock": True}
        elif service == "turn_off":
            dev["state"] = "off"
            return {"entity_id": entity_id, "state": "off", "mock": True}
        elif service == "turn_on" and domain == "light":
            dev["state"] = "on"
            dev["brightness"] = data.get("brightness", 255)
            return {"entity_id": entity_id, "state": "on", "brightness": dev["brightness"], "mock": True}
        elif domain == "climate":
            dev["state"] = "on"
            dev["temperature"] = data.get("temperature", 26)
            return {"entity_id": entity_id, "state": "on", "temperature": dev["temperature"], "mock": True}
        elif domain == "cover":
            if service == "open_cover":
                dev["state"] = "open"
                dev["position"] = 100
            elif service == "close_cover":
                dev["state"] = "closed"
                dev["position"] = 0
            return {"entity_id": entity_id, "state": dev["state"], "mock": True}
        return {"entity_id": entity_id, "state": dev["state"], "mock": True}

    def turn_on(self, entity_id: str) -> dict:
        return self.call_service("homeassistant", "turn_on", {"entity_id": entity_id})

    def turn_off(self, entity_id: str) -> dict:
        return self.call_service("homeassistant", "turn_off", {"entity_id": entity_id})

    def set_light_brightness(self, entity_id: str, brightness: int) -> dict:
        return self.call_service(
            "light", "turn_on",
            {"entity_id": entity_id, "brightness": brightness}
        )

    def get_device_state(self, entity_id: str) -> dict:
        if self._mock:
            dev = self._mock_devices.get(entity_id)
            if dev:
                return {"entity_id": entity_id, "state": dev["state"], "mock": True}
            return {"error": "设备不存在"}
        states = self.get_states()
        for s in states:
            if s.get("entity_id") == entity_id:
                return s
        return {}

    @property
    def is_configured(self) -> bool:
        return True  # Mock 模式下也返回 True，让 LLM 知道工具可用


# 工具描述，用于注入 LLM 系统提示
HA_TOOLS_DESC = """
你可以调用以下智能家居工具来控制设备：

1. turn_on(entity_id: str) - 打开设备
   示例：turn_on("light.living_room")

2. turn_off(entity_id: str) - 关闭设备
   示例：turn_off("light.living_room")

3. set_light_brightness(entity_id: str, brightness: int) - 调节灯光亮度 (0-255)
   示例：set_light_brightness("light.living_room", 200)

4. get_device_state(entity_id: str) - 查询设备状态

5. set_climate_temperature(entity_id: str, temperature: float) - 设置空调温度
   示例：set_climate_temperature("climate.living_room_ac", 26)

如果需要调用工具，请在回复末尾以 JSON 格式输出调用指令，格式如下：
```tool_call
{"tool": "turn_on", "params": {"entity_id": "light.living_room"}}
```
"""
