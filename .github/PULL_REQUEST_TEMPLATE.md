## OpenSpec

- Change: `openspec/changes/____/` 或已归档 `openspec/changes/archive/____/`（小改豁免请说明）
- Tasks 完成：__ / __

## Review 摘要（必填，便于扫 diff）

> 规范：[code-quality.md](docs/tech/code-quality.md) · 建议单 PR ≤ **5 个文件**

| 项 | 内容 |
|:---|:-----|
| **层级** | 例：Router / Service / Repository / cache / web components |
| **文件数** | __ 个（若 >5 请说明原因） |
| **职责一览** | `path` — 一句话 |

```
（粘贴 Agent 输出的 Review 摘要，或自行填写）
```

## 代码质量（Author 自检）

- [ ] 遵循目录分层（[BE](docs/tech/BE-engineering.md) / [FE](docs/tech/FE-engineering.md)）
- [ ] 一函数一事；关键分支/异常有「为什么」注释
- [ ] 无未使用依赖、无与 PR 无关的改动
- [ ] 复杂逻辑已拆到可单测函数 / Hook / `cache/` / `lib/`

## 实现说明

-

## 测试

- [ ] `pnpm lint`（`apps/web` 改动时）
- [ ] `pnpm test:api:harness`（`apps/api` 改动时；CI 同名 job 应绿）
- [ ] `bash scripts/api.sh exec pytest tests/unit -q`（有 unit 时）
- [ ] 手动：

## 关联

- Epic: EP__ Story __.__
- OpenSpec archive：merge 后作者执行 `/opsx:archive`（若尚未归档）
