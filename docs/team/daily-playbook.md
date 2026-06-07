# MemoryOS 日常 playbook（简化版）

> **觉得工具太多时，只读这一篇。**  
> 原则：**一个阶段只激活 2～3 个入口**，其余当参考书。

---

## 1. 先分清：哪些是「重复的」

### OpenSpec（4 条命令 = 4 个 skill，**二选一即可**）

| 入口                    | 位置                                  | 建议                                               |
| :---------------------- | :------------------------------------ | :------------------------------------------------- |
| **Cursor 命令（推荐）** | `.cursor/commands/opsx-propose.md` 等 | 聊天输入 `/opsx-propose`（或 Cursor 命令面板同名） |
| Cursor Skills           | `.cursor/skills/openspec-*`           | **不必 @**，与命令做同一件事                       |

**你只需要记住 3 个命令：**

```text
/opsx-propose   → 开工前：建 change、写 proposal/tasks → **停，等人审 §0**
/opsx-apply     → 人审通过后：按 tasks 逐条做
/opsx-archive   → 做完后：归档 change
```

`/opsx-explore`：**仅**需求完全不清时用，平时**忽略**。

### Superpowers（插件 / 外部 skills）

| 作用                          | 和 OpenSpec 关系                               |
| :---------------------------- | :--------------------------------------------- |
| brainstorm、plan、TDD、review | 见下表 |

**简化规则（与 [code-quality.md](../tech/code-quality.md) 一致）：**

- **有 OpenSpec `tasks.md`** → 用 **`/work-next`**；可跳过 **brainstorm/plan**，**不跳过** API 的 harness/TDD 与 verification。
- **需求很模糊** → Superpowers **brainstorm**，结论写入 OpenSpec `design.md`。

### Harness

| 你要做的         | 命令                    |
| :--------------- | :---------------------- |
| 日常开发（推荐） | `pnpm dev` 或 `pnpm dev:stack`（db + 前后端） |
| 仅起数据库       | `pnpm db:up`            |
| task 开工前      | `pnpm branch:task <change> [task-id]` |
| change 集成分支  | `pnpm branch:change <change>` |
| API 改完、提交前 | `pnpm test:api:harness` |

Harness L2/L3 等 EP02 再说。

### Cursor 内置 / 全局 Skills（`~/.cursor/skills-cursor/`）

**默认全部不用 @。** 只有下表场景才用：

| 场景               | 可 @ 的 skill                           |
| :----------------- | :-------------------------------------- |
| 盯 PR、修 CI、合并 | `babysit`                               |
| 改 Cursor 规则     | `create-rule`                           |
| 写新 skill         | `create-skill`                          |
| 其他               | **不用**（loop、canvas、split-to-prs…） |

### 本项目文档（不是「工具」，是地图）

| 何时打开       | 文档                                    |
| :------------- | :-------------------------------------- |
| EP02 七阶段顺序 | `openspec/changes/ep02-program/tasks.md` |
| 不知道本周干啥 | `docs/tasks/epics/EP02-*.md`（EP04 前做完 Program） |
| 概念忘了       | `docs/tech/ai-collab-stack.md`          |
| 规范/PR 怎么写 | `docs/tech/ai-collab-best-practices.md` |
| 新人带团队     | `docs/team/onboarding.md`               |
| **每天执行**   | **本文 `daily-playbook.md`**            |

---

## 2. 一张图：你真正的工作流

```text
                    ┌─────────────────────────┐
                    │ docs/tasks/epics/EP03   │  ← 本周目标（Build）
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │ /opsx-propose           │  ← 只做一次 / 每个 change
                    │ (openspec/changes/...)  │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │ **人审 tasks.md §0**    │  ← 必做；AI 在此停止
                    │ Task Review Gate        │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │ pnpm branch:task …      │  ← 当前 task 工作分支
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼────────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │ 读 L01 §3 30min  │  │ Cursor 写码  │  │ (可选)       │
    │ PostgreSQL 概念  │  │ 一次 1 task  │  │ Superpowers  │
    └──────────────────┘  └──────┬──────┘  │ brainstorm   │
                                   │         └─────────────┘
                    ┌──────────────▼──────────────┐
                    │ pnpm test:api:harness       │  ← Harness（提交前）
                    │ git commit                  │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ /opsx-archive + 勾 epic     │
                    └─────────────────────────────┘
```

**Learn（L01）**：嵌在 EP03 对应 Story 里读，**不要**先读完 L01 再写代码。

---

## 3. 接下来 2 周：按天做什么（EP03 + 少量 L01/L00）

### 第 1 步（今天，约 1～2h）— 只碰 OpenSpec + 1 条命令

1. 终端：`openspec update`（已 init 则只 update）
2. Cursor 新对话，**只发一句**：

   ```text
   /opsx-propose ep03-data-storage
   请根据 docs/tasks/epics/EP03-data-storage.md 生成 proposal、design、tasks，
   范围先做 Story 3.1 和 3.2。
   ```

3. 你**人工读** `openspec/changes/ep03-data-storage/proposal.md` 和
   `tasks.md`，改到满意。
4. **今天到此为止**，不写业务代码。

**不要**：开 Superpowers、@ 四个 openspec skills、读完整 L00。

---

### 第 2 步（第 1～2 天）— Story 3.1 PostgreSQL

| 顺序 | 动作                                                                                                     | 工具       |
| :--: | :------------------------------------------------------------------------------------------------------- | :--------- |
|  1   | 读 L01「PostgreSQL + SQLAlchemy」§3 前 3 个小节（📖，约 30min）                                          | L01        |
|  2   | 对 Cursor 说：「实现 openspec change ep03-data-storage 的 tasks 里关于 Docker Compose 和表设计的那几条」 | 普通 Agent |
|  3   | 自己跑 `pnpm db:up`、检查表                                                                              | 终端       |
|  4   | 写 `docs/database.md`                                                                                    | 文档       |
|  5   | 在 `tasks.md` 和 EP03 勾选 Story 3.1                                                                     | 勾选       |

**Harness**：Story 3.1 若无 API 行为变更，可只跑现有 health；有新 API 再补 L1。

---

### 第 3 步（第 3～5 天）— Story 3.2 SQLAlchemy

| 顺序 | 动作                                                         | 工具    |
| :--: | :----------------------------------------------------------- | :------ |
|  1   | 读 L01 §2 里 `Depends(get_db)`、异步 Session（📖，边做边读） | L01     |
|  2   | 每次只做 **tasks.md 里 1 条**（例如「加 async engine」）     | Cursor  |
|  3   | 每完成 1～2 条 → `pnpm test:api:harness`                     | Harness |
|  4   | `git commit`，message 带 `feat(api):`                        | git     |

**可选 Superpowers**：仅当 `get_db` 连不上、设计纠结时，用 **brainstorm**
15 分钟，不要整段 EP03 交给它。

---

### 第 4 步（第 2 周）— Story 3.3～3.4

同样模式：

1. 更新 OpenSpec `tasks.md`（或 `/opsx-propose` 子 change `ep03-redis-jwt`
   若拆开了）
2. L01 §4 Redis、JWT（📖 各 30min）
3. 一次 1 task 实现
4. 提交前 `pnpm test:api:harness` + 补 L1 测试（401、/me 等）

---

### 第 5 步（EP03 收尾）

```text
/opsx-archive ep03-data-storage
```

勾选 EP03、L00 里与 OpenSpec/Harness 相关的 🔧、L01 §3–§4 的 📖。

---

## 4. Learning 怎么不膨胀

| 轨道       | 本周只勾这些                                                |
| :--------- | :---------------------------------------------------------- |
| **Build**  | EP03 Story 3.1 → 3.2（优先），3.3/3.4 有余力再做            |
| **Learn**  | L01 §3、§4 + §2 的 `Depends`/`async`（与 3.2 同步）         |
| **Collab** | L00 只勾：OpenSpec propose/archive、Harness 跑通（各 1 条） |
| **忽略**   | L00 面试话术、L2/L3 Harness、Superpowers 全部技能列表       |

**L00 不是每周必读**，Collab 能力在 EP03 里**练一次**即可。

---

## 5. 给 Cursor 的「万能提示词」（复制即用）

### 开工某一天

```text
当前 change：openspec/changes/ep03-data-storage/
请只完成 tasks.md 中编号 【粘贴一条，如 3.2.1】。
约束：遵循 docs/tech/BE-engineering.md 分层；改完列出要跑的测试。
不要一次实现整个 Story。
```

### 提交前

```text
我已完成 【task 编号】，请帮我：
1. 运行 pnpm test:api:harness 并修失败项
2. 建议 Conventional Commits 的 subject
```

### 需求不清时（才用）

```text
/opsx-explore
EP03 里 users/conversations/messages 表字段是否合理？参考 docs/project-description.md
```

---

## 6. 工具数量对照（心理减负）

| 你以为有很多                   | 实际每天只用                              |
| :----------------------------- | :---------------------------------------- |
| 4 openspec skills + 4 commands | **3 条命令**（propose / apply / archive） |
| 14 Superpowers skills          | **0～1 个**（仅 brainstorm）              |
| Harness 三层                   | **1 条命令** `pnpm test:api:harness`      |
| 20+ Cursor 全局 skills         | **0**（PR 时才 babysit）                  |
| L00～L08                       | **L01 两节** + epic 勾选                  |

---

## 7. 本地 dev 排障（端口占用）

`pnpm dev:stack` 会并行起 **API :8000**、**Web :3000**，并确保 **PostgreSQL :5432**、**Redis :6379**（Docker）可用。

### 7.1 查看谁在监听

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN   # FastAPI / uvicorn
lsof -nP -iTCP:3000 -sTCP:LISTEN   # Next.js
lsof -nP -iTCP:5432 -sTCP:LISTEN   # PostgreSQL（多为 com.docker）
lsof -nP -iTCP:6379 -sTCP:LISTEN   # Redis（多为 com.docker）
```

`COMMAND` / `PID` 列即占用进程；`node` 多为前端，`Python` + `uvicorn` 多为 API。

### 7.2 `Address already in use`（最常见）

终端出现：

```text
ERROR: [Errno 48] Address already in use
```

表示 **端口已被占用**（常常是上次 `dev:stack` 未关干净）。**不是** LangGraph 的 `LangChainPendingDeprecationWarning` 导致——那条可忽略。

**先判断服务是否已在跑：**

```bash
curl -s --max-time 3 http://127.0.0.1:8000/api/v1/health
curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 http://127.0.0.1:3000
```

若 health 返回 `{"code":0,...}`、Web 为 `200`，可直接用 http://localhost:3000 ，**不必再起一份**。

### 7.3 干净重启（结束旧进程）

```bash
# 将 <PID> 换成 lsof 输出的数字
kill <PID>

# 普通 kill 无效时（进程卡死、占端口不响应）
kill -9 <PID>
```

然后：

```bash
pnpm dev:stack
```

**只重启某一端：**

```bash
pnpm dev:api    # 仅 API :8000
pnpm dev:web    # 仅 Web :3000
pnpm db:up      # 仅 Docker（Postgres + Redis）
```

### 7.4 其它现象

| 现象 | 处理 |
|:-----|:-----|
| API 占 8000 但 `curl` health 超时 | 多为僵尸 uvicorn → `kill -9` 后 `pnpm dev:api` |
| Docker 容器已在跑 | `pnpm db:up` 显示 Running 即可，无需重复起 |
| 改 API 代码不生效 | 确认带 `--reload`（`pnpm dev:api` 默认有）或重启 API |
| 想换 API 端口 | `apps/api/.env` 的 `PORT`，并同步 `apps/web/.env.local` 的 `NEXT_PUBLIC_API_URL` |

更细的后端 FAQ 见 [python-getting-started.md](../tech/python-getting-started.md) §6。

### 7.5 前端性能（本地）

**默认「仅 poor 告警」**——`needs-improvement` 不打扰；同页同指标 **session 内只报一次**（不发 HTTP，避免 `/api/dev/vitals` 拖慢 dev server）：

| 渠道 | 你会看到什么 |
|:-----|:-------------|
| **浏览器 Console** | `[WebVitals ⚠] /chat LCP=3200ms (poor)` |
| **页面角标** | 仅 poor 时右下角小条 12s，可点 × |

需要连 `needs-improvement` 也看：`.env.local` 加 `NEXT_PUBLIC_WEB_VITALS_VERBOSE=1` 后重启 Web。

| 方式 | 命令 / 操作 |
|:-----|:------------|
| Lighthouse `/chat` | 先起 Web，再 `pnpm lighthouse:chat` → 报告在 `apps/web/.lighthouse/chat.html` |

---

### 7.6 Commit 前必做 Code Review

实现 + Verify（lint/build/harness）通过后，**先 code review，再 commit**：

1. Agent 输出 review 结论（Critical / Important 须修完）。
2. 你确认或要求改动。
3. 你说 **「commit」** 后才提交（每 task 一个 commit 仍推荐）。

细则：`.cursor/skills/work-next/coding-constraints.md` §Commit 前 Code Review Gate。

---

## 8. 相关链接

- [onboarding.md](./onboarding.md) — 组队与新人
- [ai-collab-best-practices.md](../tech/ai-collab-best-practices.md)
  — 细节与反模式
- [EP02-streaming-chat.md](../tasks/epics/EP02-streaming-chat.md) — 当前 Build 主线（Program Phase 7 起）
