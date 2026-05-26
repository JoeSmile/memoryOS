# OpenSpec `tasks.md` 模板

> propose 时复制到 `openspec/changes/<name>/tasks.md`。  
> 与 [code-quality.md](./code-quality.md) 对齐：**一条 task ≈ 一次 review / 一个 checkpoint commit**。

---

## §0 Human review（apply 前必过 — propose 后 AI 必须停在这里）

> **禁止** propose 完成后同会话直接写业务代码。人审勾选前，仅允许改 OpenSpec 文档。

- [ ] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist（人审时可对照）

- [ ] 前后端 scope 成对（例：有 `auth/register` API → tasks 含注册页，不能只有登录页）
- [ ] design 里每条 Scenario 有对应 task 或 Harness
- [ ] 与 `docs/tasks/epics/` Story 勾选一致；无遗漏、无 scope 膨胀
- [ ] 每条 task ≤3 文件 / ~150 行，预计层正确

**Reviewer notes:**（可选）

---

## 写法约定

- 每条 task 用 `- [ ] X.Y 描述`（apply 阶段勾选 `- [x]`）。
- **粒度**：半天内可完成；**≤3 个文件** 或 **~150 行** diff；超出则拆条。
- 每条末尾用 HTML 注释或子 bullet 标 **预计文件 / 层**（propose 时写清，apply 时对照）。

---

## 模板（复制后改）

```markdown
## 1. <分组名，如 Infrastructure>

- [ ] 1.1 <动词开头，可验证>
  - 预计文件：≤2 · 层：`api` / `services` / …
  - 示例：`apps/api/app/core/redis.py`

- [ ] 1.2 …

## 2. <分组名>

- [ ] 2.1 …
  - 预计文件：…
  - Harness：`tests/harness/test_*_contract.py`（若动 API 契约）

## 3. Tests & docs

- [ ] 3.1 Harness / unit 绿灯
- [ ] 3.2 更新 `docs/` 或 epic 勾选
```

---

## 示例（节选）

```markdown
## 2. JWT API

- [ ] 2.1 新增 `POST /api/v1/auth/login` 与 schemas
  - 预计文件：3 · 层：Router + schemas + `services/auth_service.py`
  - Harness：先写 `test_auth_contract.py`（TDD）

- [ ] 2.2 Bearer 依赖 `get_current_user`
  - 预计文件：2 · 层：`core/deps.py` + 受保护路由

## 3. Frontend

- [ ] 3.1 登录页 `/login`
- [ ] 3.2 注册页 `/register`（与 register API 成对）
- [ ] 3.3 `lib/api-client.ts` Bearer + 401
```

---

## 与 work-next 的关系

| 阶段 | 动作 |
|:-----|:-----|
| propose | 用本模板拆 task（**含 §0**），写清「预计文件」→ **Task Review Pack → 停止** |
| 人审 | 你改 `tasks.md`，勾选 §0 或说「tasks 人审通过」 |
| apply | 一次只做一条 → Review 摘要 → **checkpoint commit**（用户要求时） |
| PR | 从 Review 摘要粘贴到 [PR 模板](../../.github/PULL_REQUEST_TEMPLATE.md) |
