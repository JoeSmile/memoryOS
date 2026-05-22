# EP00 — AI 协作工程化（Superpowers · OpenSpec · Harness）

| 属性         | 值                                                           |
| :----------- | :----------------------------------------------------------- |
| **周期**     | 第 1 周起，贯穿 12 周                                        |
| **优先级**   | P0（与 EP03 并行，**建议在 EP03 写库前完成 Story 0.1–0.2**） |
| **状态**     | 🟡 进行中                                                    |
| **学习路线** | [L00-ai-collab-stack.md](../learning/L00-ai-collab-stack.md) |
| **目标文档** | [ai-collab-stack.md](../../tech/ai-collab-stack.md)          |

---

## 定位

第三条轨道 **Collab**，与 `docs/tasks/epics` 的 Build、learning 的 Learn 并列：

```text
OpenSpec（对齐做什么）→ Superpowers（约束怎么做）→ Harness（证明做对）
```

带队时：本文 + `ai-collab-stack.md` §6 即团队 SOP 初版。

---

## Story 0.1 工具安装与初始化

- [x] 本机安装 OpenSpec CLI（`npm i -g @fission-ai/openspec`）
- [x] 仓库根 `openspec init` + `openspec update`（生成 `openspec/`）
- [x] `openspec/config.yaml` 写入 MemoryOS 上下文（Monorepo、`apps/api`
      Python、`pnpm` 脚本、FE/BE 文档链接）
- [x] Cursor 可执行 `/opsx:propose`（试一次 `ep03-data-storage`）

## Story 0.2 Superpowers 接入

- [ ] Cursor 安装 Superpowers（Plugin Marketplace 或官方 skills 路径）
- [ ] 团队约定：P0 Story 开工前 **brainstorm 或 plan**（记录在 OpenSpec
      proposal 或 issue）
- [ ] 在 `CONTRIBUTING.md` 或 PR 模板中链接
      [ai-collab-stack.md](../../tech/ai-collab-stack.md)

## Story 0.3 OpenSpec 与 EP03 首次闭环

- [x] `/opsx:propose "ep03-data-storage"`：proposal、design、tasks 与
      [EP03](./EP03-data-storage.md) 对齐
- [x] 实现 EP03 Story 3.1–3.2 时按 `tasks.md` 勾选（可用 `/opsx:apply`）
- [x] 完成后 `/opsx:archive`，主 spec 与 `docs/database.md` 一致

## Story 0.4 Harness 基线

- [x] 创建 `apps/api/tests/harness/` + `README.md`
- [x] L1：`test_health_contract.py`（状态码、`code/message/data` 结构）
- [x] 根目录 `pnpm test:api:harness` + `test_conversations_contract.py`
- [ ] （可选）CI 占位：EP08 前在 GitHub Actions 跑 harness

## Story 0.5 贯穿史诗的协作节奏（持续）

- [ ] EP02 起：每个史诗至少 1 个 OpenSpec change 名登记在 epic 文首
- [ ] EP02 起：流式 / Agent 功能补 Harness L1（schema）+ L2 说明
- [ ] EP10：整理 `openspec/changes/archive/` 作面试「工程化」素材

---

## 同步学习

- [ ] [L00](../learning/L00-ai-collab-stack.md) §1 OpenSpec
- [ ] [L00](../learning/L00-ai-collab-stack.md) §2 Superpowers
- [ ] [L00](../learning/L00-ai-collab-stack.md) §3 Harness
- [ ] [L00](../learning/L00-ai-collab-stack.md) §5 带团队话术

---

## 与 EP03 的顺序建议

| 顺序 | 内容                                                 |
| :--: | :--------------------------------------------------- |
|  1   | EP00 Story **0.1–0.2**（约半天）                     |
|  2   | OpenSpec **propose** `ep03-data-storage`             |
|  3   | EP03 Build（Docker、表、ORM）+ Superpowers 小步 plan |
|  4   | EP00 Story **0.4** harness 与 health 同步            |
|  5   | EP03 收尾 + OpenSpec **archive**                     |
