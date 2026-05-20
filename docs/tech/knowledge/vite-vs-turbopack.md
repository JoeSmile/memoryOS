# Vite vs Turbopack 对比笔记

> **术语**：Turbo = **Turbopack**（Next.js 打包器），不是 Turborepo。  
> **本项目版本**：`next@15.5.18`（见 `apps/web/package.json`）

从 **定位、架构、冷启动、HMR、生态、选型、版本差异** 整理。

---

## 0. Turbopack 按 Next.js 版本（官方演进）

| Next.js 版本 | `next dev` | `next build`（生产） |
|:-------------|:-----------|:---------------------|
| **15.0** | Turbopack **稳定**（需 `--turbopack` 或后续默认 dev） | **Webpack 默认** |
| **15.3** | Turbopack | 实验性 build（`--turbopack`） |
| **15.5** | Turbopack | **`--turbopack` Beta**（可选，**非默认**） |
| **16.0+** | Turbopack **默认** | Turbopack **默认**；回退 Webpack 用 `--webpack` |

**MemoryOS（15.5.18）现状**：

```json
"dev": "next dev --turbopack",
"build": "next build"
```

- 开发：日志显示 `Next.js 15.5.18 (Turbopack)` ✅  
- 生产默认：`next build` → **Webpack**（标题无 Turbopack）  
- 生产可选：`next build --turbopack` → **Turbopack Beta**（EP08 前需在 CI 实测）

---

## 1. 定位与关系

| | Vite | Turbopack |
|:---|:-----|:----------|
| **是什么** | 通用 dev + 打包 | **仅** Next.js 内置 |
| **框架** | 多框架 | Next.js only |
| **生产** | Rollup | 随 Next 版本见上表 |

**一句话**：Vite = 通用跑车；Turbopack = Next 专用引擎（dev 在 15.5 已成熟，production 在 16 才默认）。

---

## 2. 底层架构

### Vite

- 开发：浏览器 ESM + 依赖预构建（esbuild）
- 生产：Rollup

### Turbopack

- Rust + SWC + 增量依赖图
- 与 RSC / App Router 同一套图编译（Vite 硬接 Next 坑多）

---

## 3. 冷启动（趋势参考，非 SLA）

> Benchmark 为社区数据（Next 15 / Vite 6），仅作量级判断。

| 规模 | Vite | Turbopack (dev) |
|:-----|:-----|:------------------|
| 小 | 常更快 | 略慢 |
| 大 | 明显慢 | 明显快 |

---

## 4. HMR

| | Vite | Turbopack (Next dev) |
|:---|:-----|:---------------------|
| 机制 | ESM + HMR WebSocket | 增量图 |
| RSC | 需额外适配 | Next 原生 |

---

## 5. 生态

| | Vite | Turbopack |
|:---|:-----|:----------|
| 插件 | 极多 | 无 webpack 插件；用 `turbopack` 配置 |
| 定制 webpack | 成熟 | Next 16 起自定义 `webpack()` 与默认构建冲突需注意 |

---

## 6. 怎么选

- **非 Next** → Vite  
- **Next 15.5（本项目）** → dev 用 Turbopack；生产默认 Webpack，尝鲜再开 `--turbopack`  
- **Next 16+** → 默认 Turbopack，例外用 `--webpack`

---

## 7. 面试一句话（带版本）

> **15.5**：Turbopack 主导开发体验；生产默认仍是 Webpack，可用 `next build --turbopack` 走 Beta。  
> **16+**：Turbopack 成为 dev 与 build 的默认打包器。

---

## 相关

- [nextjs15.md](./nextjs15.md)
- [FE-engineering.md §3.1](../FE-engineering.md#31-turbopack-与-webpack按-nextjs-版本)
- [官方 Turbopack](https://nextjs.org/docs/app/api-reference/turbopack)
