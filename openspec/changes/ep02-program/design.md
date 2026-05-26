## Context

- EP03 核心（PG/Redis/JWT）已完成；`ep03-db-optimize`、`ep02-chat-sse` 等已 propose。
- 项目原则：对话编排走 **LangGraph**，可观测走 **LangSmith**；SSE 为 EP02 传输层。

## Goals / Non-Goals

**Goals:**

- 固定 **7 Phase** 顺序（见 `tasks.md`）。
- 每 Phase 有明确 **Done 定义**（子 change archive + 验证命令）。
- Phase 2 学习产出可审查（文档草稿，无生产图代码）。

**Non-Goals:**

- 本 change 不产生 `apps/` 代码。
- 不在此 change 内实现 EP04 RAG。

## Decisions

### D1: Phase 顺序

```text
1 ep03-db-optimize
2 LangGraph 学习（L02 §5 + langgraph-chat.md 草稿）
3 LangSmith 环境（并入 Phase 4 首 task）
4 ep02-langgraph
5 ep02-chat-sse（SSE 接 Graph）
6 ep02-chat-sse 前端 4.x（最小 /chat，属 Phase 5 change 内）
7 ep02-chat-ui（侧栏 + Markdown + Zustand）
```

Phase 6 不单独开 change，避免过碎；在 program 里作为 Phase 5 的完成条件之一。

### D2: 与其它 epic 的栅栏

- EP04+ **禁止**新开 apply，直到 `ep02-program` tasks 全部 `[x]` 并 archive `ep02-program`。

### D3: 子 change 人审

- 每个子 change 仍走 **Task Review Gate §0**；program Phase 勾选在子 change archive 之后。

## Risks / Trade-offs

| 风险 | 缓解 |
|:-----|:-----|
| program 与子 change 重复 | program 只保留 Phase 级 checkbox |
| 学习 Phase 难自动化 | Done = 文档路径 + L02 勾选截图/自述 |

## Migration Plan

1. 人审 `ep02-program/tasks.md` 及子 change proposals。
2. `/work-next ep03-db-optimize` 开始 Phase 1。
