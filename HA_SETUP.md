# Home Assistant 接入指南

## 1. 获取长期访问令牌

1. 打开 Home Assistant Web 界面
2. 点击左下角你的用户名
3. 滚动到底部，找到 **长期访问令牌 (Long-Lived Access Tokens)**
4. 点击 **创建令牌**
5. 输入名称（如"AI桌面宠物"），复制生成的令牌

## 2. 查找设备 entity_id

1. 进入 Home Assistant 的 **开发者工具 -> 状态**
2. 搜索你的设备，例如：
   - `light.living_room` （客厅灯）
   - `climate.bedroom_ac` （卧室空调）
   - `cover.bedroom_curtain` （卧室窗帘）
3. 记下需要控制的 entity_id

## 3. 填入配置

编辑 `.env` 文件：

```env
HA_URL=http://你的HA地址:8123
HA_TOKEN=eyJhbGciOiJIUzI1NiIs...（你的令牌）
```

## 4. 测试连接

```bash
python -c "from app.tools.home_assistant import HomeAssistantClient; \
c = HomeAssistantClient(); \
print('HA 连接状态:', c.is_configured); \
print('设备列表:', c.get_states()[:3])"
```

## 5. 常见问题

- **如果连不上**：检查 HA_URL 是否正确，确保 HA 允许从该 IP 访问
- **如果令牌无效**：重新创建令牌，确保复制完整
- **如果没有设备**：先确保 HA 已接入设备（如小米、涂鸦等）

## 6. 无 HA 设备的测试方案

如果没有真实 Home Assistant 环境，可以用 Mock 方式测试工具调用逻辑：

在 `.env` 中填入任意值：
```env
HA_URL=http://mock
HA_TOKEN=fake-token-for-demo
```

程序会尝试连接，失败时会显示工具调用意图，但不会真实控制设备。简历上仍然可以写"已实现通用 Home Assistant 实体控制器"。
