# @memoryos/shared

跨应用共享的 **TypeScript 类型、常量与纯函数工具**，无 React 运行时依赖。

## 职责

- API 请求/响应类型（Session、Message、Knowledge…）
- 全局常量（模型名、分页默认值、错误码）
- 通用工具（日期格式化、Token 估算封装等）

## 使用

```ts
import { APP_NAME } from "@memoryos/shared";
```

## 目录结构

```
packages/shared/
└── src/
    └── index.ts    # 统一导出入口
```

## 说明

- 仅包含与 UI 无关的逻辑，避免循环依赖
- 由 `apps/web` 通过 pnpm `workspace:*` 引用
