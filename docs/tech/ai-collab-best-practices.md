# OpenSpec · Superpowers · Harness 最佳实践（MemoryOS）

> 与 [ai-collab-stack.md](./ai-collab-stack.md)（概念与安装）配合阅读。  
> 本文：**怎么做得好**、**怎么避免翻车**、**多人如何协作**。

---

## 0. 黄金法则（四条）

1. **没有 change，没有大 PR** — 超过 3 个文件或跨 `apps/web` + `apps/api`
   的改动，必须先有 OpenSpec change（或 epic 已拆好的 Story）。
2. **没有 plan，不让 AI 写业务** — 用 Superpowers 或 OpenSpec `tasks.md`
   列出小步；禁止「帮我实现整个 EP03」。
3. **没有 Harness 绿，不合并 API/Agent**
   — 至少 L1；EP02+ 的 LLM 路径必须有 L2 说明或 waived 理由（Tech Lead 批准）。
4. **单 task 可 review** — 用 **`/work-next`**（代码五条见 [code-quality.md](./code-quality.md) §1；体量/停步见 work-next，不在此重复）。

---

## 1. OpenSpec 最佳实践

### 1.1 什么时候必须 propose

| 场景                         | 要不要 OpenSpec change                       |
| :--------------------------- | :------------------------------------------- |
| 修 typo、改文档链接          | 否                                           |
| 单文件 bugfix（行为不变）    | 否，PR 说明即可                              |
| 新 API、新表、新页面、改协议 | **是**                                       |
| 跨端功能（web + api）        | **是**                                       |
| 重构模块边界                 | **是**                                       |
| 不确定范围                   | **是**（宁可多 proposal 一小时，少返工一天） |

### 1.2 Change 命名规范

```text
ep03-data-storage          # 与史诗对齐，推荐
ep02-chat-sse-chunk        # 功能 + 技术点
fix-jwt-refresh-expiry     # 修复也可单独 change
```

- 全小写、连字符、**一个 change = 一个可合并单元**（目标 1–3 天完成）。
- 超大史诗拆多个 change：`ep04-rag-upload`、`ep04-rag-retrieve`。

### 1.3 标准工作流

```text
/opsx:propose "ep03-data-storage"
  → 人读 proposal.md、design.md（可评论修改）
  → 确认 tasks.md 与 docs/tasks/epics/EP03 一致
/opsx:apply（或人工按 tasks 实现，逐条勾选）
  → 实现中 scope 变了：回到 change 改 design/tasks，不要只改代码
/opsx:archive
  → openspec/specs 更新，change 进 archive/
```

### 1.4 `openspec/config.yaml` 应包含什么（MemoryOS）

```yaml
# 示例 — init 后按项目填写，见 docs/tech/openspec-config.example.yaml
context: |
  Monorepo: apps/web (Next.js 15), apps/api (FastAPI), packages/shared, packages/ui.
  Python 3.11+ in Conda env memoryos-api. Root scripts: pnpm dev:web, pnpm dev:api.
  API response: { code, message, data }. Docs: docs/tech/FE-engineering.md, BE-engineering.md.
rules:
  - Propose before multi-file features.
  - Match epic tasks in docs/tasks/epics/.
```

- **拉代码后**执行 `openspec update`，保证 Cursor slash 命令最新。
- **不要**在 change 里写密钥；敏感项只引用 `.env.example` 变量名。

### 1.5 Review 检查清单（Author & Reviewer）

- [ ] proposal 写清了 **Why / What / Out of scope**
- [ ] design 标了影响的目录（`apps/api/...`、`apps/web/...`）
- [ ] tasks 可勾选、粒度 ≤ 半天，每条含 **预计文件 / 层**（见 [openspec-tasks-template.md](./openspec-tasks-template.md)）
- [ ] 与 epic Story 编号能对应（如 EP03 Story 3.2）
- [ ] 合并前已 archive 或 PR 说明「archive 在 merge 后由作者执行」

### 1.6 反模式（禁止）

| 反模式                   | 后果                          |
| :----------------------- | :---------------------------- |
| 只在 Cursor 聊天里定需求 | 后人无法追溯，AI 上下文丢失   |
| 一个 change 干 2 个史诗  | archive 困难、review 巨大     |
| 代码写完才补 OpenSpec    | spec 与实现不一致，失去意义   |
| 永不 archive             | `changes/` 堆满，主 spec 过时 |

### 1.7 多人协作：OpenSpec

- **一个 change 一个负责人（Owner）**；其他人 PR 进 Owner 分支或配对。
- **禁止两人同时改同一 `openspec/changes/<name>/`**
  — 像改同一份 PRD，先沟通合并文案再动。
- 并行功能用 **不同 change 名**（`ep03-redis` vs `ep03-postgres`
  可先后 archive）。
- `main`
  上只保留已 archive 的 specs + 进行中的 changes；**冲突在 proposal 阶段解决**，不要留到代码冲突。

---

## 2. Superpowers 最佳实践

### 2.1 与 OpenSpec 的分工

| 阶段                     | 用谁                                             |
| :----------------------- | :----------------------------------------------- |
| 定需求、方案、任务列表   | OpenSpec `/opsx:propose`（产出 proposal、tasks） |
| 拆执行步骤、约束 AI 写法 | Superpowers **writing-plans**                    |
| 澄清模糊需求             | Superpowers **brainstorming**                    |
| 实现每一 task            | Superpowers **TDD** + 普通编码                   |
| 合并前                   | Superpowers **code review** + 人审               |

**不要**让 Superpowers 重新发明一套与 OpenSpec tasks 矛盾的 plan；以
**`tasks.md` 为权威**，Superpowers 只细化到「下一步改哪几个函数」。

### 2.2 何时触发 Superpowers

| 必须                         | 可选           |
| :--------------------------- | :------------- |
| 新史诗第一个 Story           | 改一行样式     |
| 首次接 LangGraph / SSE / RAG | 熟悉模块的小修 |
| 一次 PR > 80 行逻辑          | 纯文档         |

### 2.3 Plan 粒度（可执行）

**好 task（AI 友好）**

```markdown
- [ ] 1.1 在 app/core/database.py 添加 async engine（读 DATABASE_URL）
- [ ] 1.2 添加 get_db Depends，yield session + finally close
- [ ] 1.3 harness: test_db_session_commits_user_fixture
```

**差 task**

```markdown
- [ ] 完成数据库层
- [ ] 做好 EP03
```

规则：**一条 task ≈ 一个提交或 30–90 分钟**；涉及多文件就拆。

### 2.4 TDD 与 AI

1. 先写/补 **Harness 或 pytest**（红）
2. 再让 AI 实现（绿）
3. 重构时禁止扩大 scope（refactor 不加功能）

对 MemoryOS：**API 优先 L1 契约**，Agent 再 L2。

### 2.5 Code Review（Superpowers + 人）

AI review 不能代替人审。合并前人必看：

- 安全：鉴权、SQL 注入、密钥
- 边界：错误处理、事务
- 与 OpenSpec design 是否一致

### 2.6 反模式

| 反模式                    | 规避                                   |
| :------------------------ | :------------------------------------- |
| 「直接帮我写完 EP03」     | 改为「执行 tasks.md 第 3.2 节第 1 条」 |
| 一次生成 10+ 文件         | 按 task 分批，每批 review              |
| 无测试的 AI 代码          | TDD：先 harness                        |
| plan 与 OpenSpec 两套任务 | 以 OpenSpec tasks 为准                 |

### 2.7 多人协作：Superpowers

- 团队统一 **Cursor + Superpowers**（或文档化等价流程：必须先贴 plan 再 PR）。
- PR 描述贴 **plan 摘要** 或链接 OpenSpec `tasks.md` 勾选截图。
- Junior 的 PR：Senior 先过 OpenSpec 再过 code，避免「AI 写错但 spec 也没审」。

---

## 3. Harness 最佳实践

### 3.1 三层怎么用

| 层     | 成本       | MemoryOS 规则                                 |
| :----- | :--------- | :-------------------------------------------- |
| **L1** | 低，毫秒级 | **每个 API PR 必跑**；`pnpm test:api:harness` |
| **L2** | 中，需 LLM | EP02+ 每个对外 LLM 行为至少 3 条 yaml case    |
| **L3** | 高         | 发布前 / 重大 Agent 改版；记录 pass rate 基线 |

### 3.2 L1 写什么

- HTTP 状态码
- 响应 JSON 字段（`code`、`message`、`data`）
- 错误体与 `exceptions.py` 一致（422/404/500）
- 鉴权失败 401（EP03.4 后）

不依赖真实 PostgreSQL / OpenAI：用 **TestClient / mock / fixture DB**。

### 3.3 L2 案例结构（EP02 起）

```yaml
# tests/harness/cases/chat_greeting.yaml
id: chat_greeting_01
input:
  messages: [{ role: user, content: "你好" }]
rubric: |
  回复应礼貌、简短；不应编造用户未提供的记忆。
min_score: 0.8
```

- rubric **版本化**；改 prompt 要改 case 或升版本。
- CI 可对 L2 设 `continue-on-error` + 夜间跑全量。

### 3.4 目录约定

```text
apps/api/tests/harness/
├── test_*_contract.py    # L1
├── cases/                # L2 yaml
├── runners/              # 评测脚本（EP02+）
└── README.md
```

命名：`test_<领域>_contract.py`、`cases/<epic>_<场景>.yaml`。

### 3.5 反模式

| 反模式               | 规避                    |
| :------------------- | :---------------------- |
| 只测 200 不测 body   | 契约测试断言 schema     |
| 测试调生产 OpenAI    | fixture / vcr / mock    |
| 无 L2 就上 Agent     | EP05 前必须有最小 L2 集 |
| 改了 prompt 从不回归 | PR 触发表里列出的 case  |

### 3.6 多人协作：Harness

- **改 API 的人负责改或扩 harness**；Reviewer 不看测试不让合。
- 基线失败：**先修回归再合 feature**（除非 epic 明确标注破坏基线并更新 case）。
- 共享 `cases/` 冲突：按 change 分目录 `cases/ep03/`、`cases/ep02/`。

---

## 4. 三件套联合作业流（最佳顺序）

```mermaid
flowchart LR
  A[epic 勾选 Story] --> B["/opsx:propose"]
  B --> C[人审 proposal/design]
  C --> D[Superpowers plan 细化 tasks]
  D --> E[Harness 红测试]
  E --> F[实现 + 绿测试]
  F --> G[Superpowers + 人 Review]
  G --> H["/opsx:archive"]
  H --> I[更新 epic 勾选]
```

### 4.1 单次功能检查表（复制到 PR）

```markdown
## OpenSpec

- [ ] Change 名：openspec/changes/\_\_\_\_
- [ ] tasks.md 已全部勾选
- [ ] merge 后 archive（或本 PR 已 archive）

## Superpowers

- [ ] 有 plan / 链到 tasks.md
- [ ] 非单次 mega diff

## Harness

- [ ] pnpm test:api:harness 通过
- [ ] （若 LLM）L2 case ID：\_\_\_\_

## Docs

- [ ] epic / docs/tech 已更新（如需要）
```

---

## 5. 规模建议（个人 vs 团队）

| 人数   | OpenSpec                       | Superpowers        | Harness                      |
| :----- | :----------------------------- | :----------------- | :--------------------------- |
| 1 人   | 每个 epic 1 change 即可        | 大功能必 plan      | 本地 `pnpm test:api:harness` |
| 2–3 人 | change Owner + 每周 sync specs | PR 必贴 plan       | PR 必绿 L1                   |
| 4+ 人  | + 每周 spec review 会          | + 统一 Cursor 规则 | + CI 跑 harness（EP08）      |

---

## 相关

- [ai-collab-stack.md](./ai-collab-stack.md) — 安装与概念
- [../team/onboarding.md](../team/onboarding.md) — 新人 onboarding
- [openspec-config.example.yaml](./openspec-config.example.yaml) — config 模板
