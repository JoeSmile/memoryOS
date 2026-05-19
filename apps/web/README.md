# @memoryos/web — 前端应用

基于 **Next.js 15**、**React**、**TypeScript**、**TailwindCSS** 的 Web 客户端。

## 技术栈

- 框架：Next.js 15（App Router）
- 语言：TypeScript
- 样式：TailwindCSS
- 状态：Zustand
- 富文本：react-markdown
- 流式：ReadableStream / SSE 客户端

## 目录约定（Story 1.3 初始化后）

```
apps/web/
├── app/              # App Router 页面与布局
├── components/       # 业务组件
├── lib/              # 工具、API 客户端
├── stores/           # Zustand stores
└── public/           # 静态资源
```

## 启动

```bash
# 在仓库根目录
pnpm dev:web

# 或在本目录
pnpm dev
```

默认地址：<http://localhost:3000>

## 环境变量

复制 `.env.example` 为 `.env.local`（Story 1.3 提供模板）：

| 变量 | 说明 |
|:-----|:-----|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址，如 `http://localhost:8000` |
