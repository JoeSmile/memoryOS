# Vite vs Turbopack 对比笔记

> **术语**：文中的 Turbo =
> **Turbopack**（Next.js 开发服务器 / 打包器），不是 Turborepo。  
> Vite 是通用构建工具，与 Next.js 无绑定，仅常作对比。

从 **定位、架构、冷启动、HMR、生态、选型、面试话术** 七个维度整理。

---

## 1. 定位与关系（最容易混淆）

|            | Vite                                | Turbopack                            |
| :--------- | :---------------------------------- | :----------------------------------- |
| **是什么** | 通用构建工具（dev server + 打包器） | Next.js 专属 dev server + 增量打包器 |
| **框架**   | Vue / React / Svelte / 原生 JS 等   | **仅** Next.js                       |
| **作者**   | Evan You 生态                       | Vercel，Rust 自研                    |

**一句话**：Vite 是「通用跑车」；Turbopack 是「Next.js 专用超跑」。

---

## 2. 底层架构（为什么快）

### Vite：Node.js + esbuild + Rollup

| 阶段           | 机制                                                    |
| :------------- | :------------------------------------------------------ |
| **开发**       | 浏览器原生 ESM，按需请求，不全量打包                    |
| **依赖预构建** | esbuild（Go）将 `node_modules` 打成少量 ESM，减少请求数 |
| **生产**       | Rollup 打包，Tree-shaking 较好                          |
| **主线程**     | Node.js；CPU 密集任务交给 esbuild 子进程                |

### Turbopack：Rust + 增量计算

| 点           | 说明                                                                               |
| :----------- | :--------------------------------------------------------------------------------- |
| **实现**     | 全栈 Rust，原生多线程，无 Node 主线程瓶颈                                          |
| **编译**     | 增量计算引擎 + SWC（Rust）                                                         |
| **更新粒度** | 只重编变更模块，依赖图增量更新，缓存细                                             |
| **生产**     | Next.js 生产仍以 `next build` 为主；Turbopack 主打 **dev**，生产路线以官方文档为准 |

---

## 3. 冷启动（项目越大差距越明显）

> 参考口径：2026 年前后社区 benchmark（Next 15 / Vite
> 6），**非官方承诺**，作趋势判断即可。

| 规模              | Vite   | Turbopack | 谁更快         |
| :---------------- | :----- | :-------- | :------------- |
| 小型（~40 组件）  | ~380ms | ~640ms    | Vite           |
| 中型（~200 组件） | ~1.1s  | ~850ms    | Turbopack 略快 |
| 大型（800+ 组件） | ~4.2s  | ~1.6s     | Turbopack 明显 |

**结论**：小项目 Vite 冷启 often 更快；**中大型 Next.js 项目**
Turbopack 优势更明显。  
MemoryOS 走 Next 15，开发用 `next dev --turbopack` 合理。

---

## 4. HMR（热更新 · 面试高频）

### Vite HMR

- 机制：原生 ESM + WebSocket，推送变更模块
- 速度：约 **10–50ms**（小项目接近即时）
- 稳定性：约 **90–95%**；复杂依赖 / CSS 边界偶发状态丢失

### Turbopack HMR

- 机制：增量依赖图 + 细粒度缓存，最小影响子树更新
- 速度：大型项目也常 **<50ms**；共享工具类变更往往更稳
- 稳定性：约 **96–99%**，接近传统 webpack 体验

### 与 Next 强相关的一点

Turbopack **原生适配** RSC、Server
Actions 等；Vite 若硬接 Next 需插件，坑多。**非 Next 项目不必强行比 HMR。**

---

## 5. 生态与插件

|          | Vite                | Turbopack                                           |
| :------- | :------------------ | :-------------------------------------------------- |
| **生态** | 官方 + 社区插件极多 | 封闭，仅 Next 内使用                                |
| **配置** | 简洁，插件 API 成熟 | 与 App Router / Image / Middleware 深度集成，少配置 |
| **适合** | 非 Next 的各类前端  | Next.js 15+ 一体化开发                              |

---

## 6. 怎么选

### 选 Vite

- 非 Next 项目（Vue、Svelte、React SPA、静态站）
- 小 / 中型项目，要极简配置 + 极速冷启
- 强依赖 Rollup 插件生态

### 选 Turbopack（本项目）

- **Next.js 15+**，`apps/web` 已启用 `--turbopack`
- 中大型代码量、长期迭代
- 深度使用 RSC / App Router / Server Actions
- 团队统一 Next 全栈，少维护 bundler 配置

---

## 7. 面试 / 述职一句话

**Vite**：通用构建工具；开发态靠原生 ESM 实现小项目极速冷启（约 300–500ms）与毫秒级 HMR；生产用 Rollup；生态成熟，适合**非 Next**
项目。

**Turbopack**：Next.js 专属 Rust 工具链；多线程 + 增量计算，**大型项目**冷启与 HMR 稳定性通常优于 Vite；深度集成 RSC；**仅适用于 Next**，是大型 Next 全栈应用的默认 dev 方案。

**核心区别**：Vite = 通用、轻量、小项目快；Turbopack =
Next 专用、大项目 dev 更稳更快。

---

## 相关

- 项目内工程说明：[FE-engineering.md §3.1](../FE-engineering.md#31-为什么-turbopack-开发时-hmr-通常快于-webpack)
