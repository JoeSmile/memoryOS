# L00 — AI 协作工程栈（Superpowers · OpenSpec · Harness）

**对应史诗**：[EP00](../epics/EP00-ai-collaboration.md)（贯穿全项目，第 1 周起步）  
**建议时间分配**：学习 40%
· 落地 60%（与 EP03 并行时，Collab 约占本周 20% 工时）  
**主文档**：[ai-collab-stack.md](../../tech/ai-collab-stack.md) ·
[ai-collab-best-practices.md](../../tech/ai-collab-best-practices.md) ·
[onboarding.md](../../team/onboarding.md)

> 勾选：📖 能讲清 · 🔧 仓库已落地（写路径）  
> **带队目标**：学完 §5 能向新成员讲清「先 spec、再纪律、再评测」。

---

## 0. 为什么要学（30 秒）

| 痛点                     | 工具        |
| :----------------------- | :---------- |
| 需求只在聊天里，改乱了   | OpenSpec    |
| AI 一次写太多、难 review | Superpowers |
| LLM 输出不稳定，不敢上线 | Harness     |

---

## 1. OpenSpec — 先对齐再写码

### 学什么

- [x] 📖 Spec vs Change：`openspec/specs` 现状 vs `openspec/changes` 提案
- [x] 📖 OPSX：`/opsx:propose` → `/opsx:apply` → `/opsx:archive`
- [x] 📖 与 `docs/tasks/epics` 的分工（史诗 vs 单次变更）
- [ ] 📖 brownfield：在已有 MemoryOS 上迭代，不是重写
- [x] 🔧 仓库根 `openspec init` + `openspec/config.yaml` 含项目上下文
- [x] 🔧 归档 change：`openspec/changes/archive/2026-05-22-ep03-data-storage/`

### 面试 / 带队常问

- 为什么不用「只在 Cursor 里口头说需求」？
- OpenSpec 和 GitHub Spec Kit 的差异？（轻量、无 rigid phase gate）
- 团队如何 review：先看 proposal 还是先看 diff？

### 实战易踩坑

| 坑                    | 现象               | 规避                   |
| :-------------------- | :----------------- | :--------------------- |
| 只 propose 不 archive | specs 与代码漂移   | 每个 PR 结束 archive   |
| change 太大           | tasks 几十条完不成 | 按 Story 拆多个 change |
| 未 `openspec update`  | slash 命令不可用   | 拉代码后跑 update      |

### 官方

- <https://openspec.dev/>
- [concepts.md](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)

---

## 2. Superpowers — AI 实现纪律

### 学什么

- [x] 📖 流程：brainstorm → plan → TDD → review → finish
- [x] 📖 与 OpenSpec 配合点：proposal 通过后再大规模 apply
- [x] 📖 subagent / worktree 适用场景（大史诗可拆）
- [x] 🔧 Cursor 已安装 Superpowers（或 skills 等价配置）
- [ ] 🔧 至少 1 次「先 plan 后写」的 EP03 或 EP01 小改动记录路径

### 面试 / 带队常问

- Superpowers 和 OpenSpec 会不会重复？（一个管 What 一个管 How）
- 如何防止 junior 跳过 TDD？（PR 模板 + review 清单）
- 单人项目是否过重？（大功能用，改一行 CSS 可不用）

### 实战易踩坑

| 坑              | 现象              | 规避                       |
| :-------------- | :---------------- | :------------------------- |
| 跳过 brainstorm | 返工多            | EP02+ 必须先澄清流式协议   |
| plan 粒度太大   | AI 一次改 10 文件 | 任务 ≤ 1 模块；见 [code-quality.md](../../tech/code-quality.md) |
| 无 review 关    | 明显 bug 进 main  | 对照 OpenSpec tasks + 每 task Review 摘要 |

### 参考

- [obra/superpowers](https://github.com/obra/superpowers)
- Cursor Forum: Superpowers integration

---

## 3. Harness — Agent 可验证

### 学什么

- [ ] 📖 Harness vs Framework（LangGraph 是框架，Harness 是运行时+测试床）
- [ ] 📖 L1 确定性 / L2 模型评分 / L3 统计 pass rate
- [ ] 📖 tool simulator：测试不调真 OpenAI、真 DB
- [x] 🔧 `apps/api/tests/harness/` + health / conversations 契约测试
- [x] 🔧 根目录 `pnpm test:api:harness`
- [ ] 📖 当前用法与局限：[`harness/README.md`](../../apps/api/tests/harness/README.md)（L2/L3 落地后再全文总结）

### 面试 / 带队常问

- 为什么传统单元测试不够？（非确定性、多步累积错误率）
- L2 评测成本怎么控？（抽样 + 小模型判分 + 缓存）
- 生产 LangSmith trace 和 Harness 关系？（trace 排障，Harness 回归）

### 实战易踩坑

| 坑               | 现象                | 规避                        |
| :--------------- | :------------------ | :-------------------------- |
| 只测 happy path  | 线上 tool 失败      | fixtures 含超时/空结果      |
| 判分 prompt 漂移 | L2 结果不稳         | rubric 版本化 yaml          |
| 与 OpenSpec 脱节 | 测的不是本次 change | tasks.md 列 harness 用例 ID |

### 参考

- [AI Agent Testing (Harness Engineering)](https://harness-engineering.ai/blog/ai-agent-testing-how-to-build-reliable-production-ready-agent-systems/)

---

## 4. 三件套协作（综合）

### 学什么

- [x] 📖 能画一张图：OpenSpec → Superpowers → Harness → merge
- [ ] 📖 MemoryOS 单次功能 DoD（见 ai-collab-stack §6）
- [x] 🔧 EP03 完整走通 propose → apply → archive

### 阶段自测（第 1–2 周末）

1. 用一句话向同事解释三者分工。
2. 演示：对一个 change 从 propose 到 archive 的路径。
3. 指出仓库里 Harness 测试文件并本地跑绿。

---

## 5. 带团队话术（可直接用）

**周会开场（5 分钟）**

> 本周每个 active
> change 报一下：OpenSpec 文件夹名、完成几条 task、Harness 是否绿。

**Review 原则**

> 没有 change 或 epic 勾选的 PR 不接；没有 L1 测试的 API
> PR 不接；AI 功能没有评测说明的不上生产。

**新人 onboarding**

> 第一天：装 OpenSpec + Superpowers，跑通 harness
> health；第二天：跟一个小 change 走完 propose→archive。

---

## 相关

- [EP00](../epics/EP00-ai-collaboration.md) · [L01](./L01-foundation.md) ·
  [tasks/README.md](../README.md)
