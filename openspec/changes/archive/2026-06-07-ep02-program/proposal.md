## Why

EP02 横跨数据优化、LangGraph、SSE、前端多模块，若并行多个 epic 易 scope 漂移（如 ep03-jwt 漏注册页）。需要 **单一顺序真相源**：7 个阶段全部完成并 archive 后，再启动 EP04+。

本 change **不直接改业务代码**，只编排子 change 与 learning 门禁。

## What Changes

- 新增 `ep02-program` 总控 `tasks.md`：**7 个大 Phase**，每 Phase 对应一个或多个子 change / 学习产出。
- 更新 EP02 史诗：OpenSpec 链接指向 program + 子 change 链。
- **团队约定**：Phase 1–7 未全部勾选前，不 propose/apply EP04、EP05 等功能 epic（EP00/EP01 维护性小改除外）。

## Capabilities

### New Capabilities

- `ep02-program`: 七阶段交付顺序与完成定义（meta）。

### Modified Capabilities

- （无 runtime spec）

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `openspec/changes/ep02-program/` | 总控 tasks |
| `docs/tasks/epics/EP02-streaming-chat.md` | 阶段表 |
| 子 change | `ep03-db-optimize`、`ep02-langgraph`、`ep02-chat-sse`、`ep02-chat-ui` |
