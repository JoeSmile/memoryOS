# Task Review Gate（人审门禁）

> **问题背景**：propose 生成 `tasks.md` 后若 AI 直接写码，易漏 scope（如 ep03-jwt 仅有登录页、缺注册页）。  
> **规则**：propose 与 apply 之间 **必须** 有一次人类审查；AI **不得** 自动跳过。

---

## 何时触发

| 场景 | 动作 |
|:-----|:-----|
| `/opsx:propose` 或 `openspec-propose` 刚完成 | **HARD STOP** — 只输出 Task Review Pack，**禁止**写业务代码 |
| `/opsx:apply`、`/work-next`、用户说「开始实现」 | **先检查** `tasks.md` §0 是否已勾选 |
| 用户说「tasks 人审通过」「继续实现」「approve tasks」 | 勾选 §0，可进入 apply |

---

## `tasks.md` 固定头部（propose 必须写入）

见 [openspec-tasks-template.md](../../../docs/tech/openspec-tasks-template.md) §0。

关键 checkbox：

```markdown
- [ ] **Tasks reviewed by human**
```

**未勾选** 且用户 **未明确批准** → Agent **停止**，输出 Task Review Pack。

---

## Task Review Pack（propose 结束时 Agent 输出）

```markdown
## Task Review Gate — `<change-name>`

**状态：** 等待人审（AI 已停止，未写业务代码）

### 产物路径
- proposal: `openspec/changes/<name>/proposal.md`
- design: `openspec/changes/<name>/design.md`
- tasks: `openspec/changes/<name>/tasks.md`

### Tasks 一览
| # | Task | 预计文件/层 |
|---|------|-------------|
| … | … | … |

### 请你核对（常见漏项）
- [ ] 前后端是否成对（例：register API ↔ register 页面）
- [ ] Harness 是否覆盖 design 里每条 Scenario
- [ ] 与 `docs/tasks/epics/` 勾选是否一致

### 下一步（你选一条）
1. 直接改 `tasks.md`，改完后说 **「tasks 人审通过」**
2. 说 **「继续实现」** — Agent 会先勾选 §0，再 `pnpm branch:task` / `branch:change`，然后 apply
3. 说 **「继续」** — 仅当 §0 已勾选时才会写码；仍应先建 task 分支
```

---

## Apply 前置检查（伪代码）

```
if tasks.md section 0 unchecked:
  if user said explicit approval (人审通过 / approve tasks / 继续实现):
    mark section 0 [x]
    proceed to task 1 only (one task per session if work-next)
  else:
    STOP — show Task Review Pack again
else:
  proceed to implement (work-next: one task then stop)
```

**Explicit approval 短语**（任一即可）：`tasks 人审通过`、`approve tasks`、`继续实现`、`tasks approved`、`开始实现`。

**不算批准**：`继续`、`work-next`、`<change-name>` 单独出现 — 若 §0 未勾选仍须 STOP。

---

## 与 ep03-jwt 教训

- design 有 register/login/me，tasks 只写「登录页」→ 漏注册 UI。  
- **Review checklist** 强制问：「有 login 是否必有 register / 有 API 是否必有对应 UI task？」
