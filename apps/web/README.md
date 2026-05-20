# @memoryos/web — 前端应用

基于 **Next.js 15**、**React 19**、**TypeScript**、**TailwindCSS v4** 的 Web 客户端。

## 技术栈

| 类别 | 技术 |
|:-----|:-----|
| 框架 | Next.js 15（App Router + Turbopack） |
| 语言 | TypeScript（路径别名 `@/*`） |
| 样式 | TailwindCSS v4（`app/globals.css` + `@theme`） |
| 规范 | ESLint 9 + Prettier + eslint-config-prettier |
| 状态 | Zustand（EP02） |
| 共享包 | `@memoryos/shared` |

## 目录结构

```
apps/web/
├── app/
│   ├── layout.tsx      # 根布局
│   ├── page.tsx        # 首页
│   ├── not-found.tsx   # 404
│   ├── chat/           # 对话（EP02 占位）
│   └── globals.css     # Tailwind v4 主题
├── public/
├── .env.example
├── next.config.ts
├── tsconfig.json
└── eslint.config.mjs
```

## 启动

```bash
# 仓库根目录
pnpm dev:web

# 或本目录
pnpm dev
```

- 开发地址：<http://localhost:3000>
- Turbopack 已启用（`next dev --turbopack`）

## 环境变量

```bash
cp .env.example .env.local
```

| 变量 | 说明 |
|:-----|:-----|
| `NEXT_PUBLIC_API_URL` | 后端 API，默认 `http://localhost:8000` |

## 脚本

| 命令 | 说明 |
|:-----|:-----|
| `pnpm dev` | 开发服务器 |
| `pnpm build` | 生产构建 |
| `pnpm start` | 生产启动 |
| `pnpm lint` | ESLint 检查 |
| `pnpm format` | Prettier 格式化 |
