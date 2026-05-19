# @memoryos/ui

跨应用复用的 **React 组件库**（按钮、输入框、消息气泡等），供 `apps/web` 引用。

## 技术栈

- React 19
- TailwindCSS（与 web 保持一致的 design tokens）
- 无业务状态，组件保持展示型 / 受控型

## 使用

```tsx
// Story 1.3 起逐步导出组件
import { /* Button */ } from "@memoryos/ui";
```

## 目录结构

```
packages/ui/
└── src/
    └── index.ts    # 组件统一导出
```

## 说明

- `peerDependencies`: `react`, `react-dom`
- 不在此包内直接请求 API；数据由 `apps/web` 传入
