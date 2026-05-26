# OpenSpec `tasks.md` 模板

> propose 时复制到 `openspec/changes/<name>/tasks.md`。  
> 与 [code-quality.md](./code-quality.md) 对齐：**一条 task ≈ 一次 review / 一个 checkpoint commit**。

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
```

---

## 与 work-next 的关系

| 阶段 | 动作 |
|:-----|:-----|
| propose | 用本模板拆 task，写清「预计文件」 |
| apply | 一次只做一条 → Review 摘要 → **checkpoint commit**（用户要求时） |
| PR | 从 Review 摘要粘贴到 [PR 模板](../../.github/PULL_REQUEST_TEMPLATE.md) |
