# packages — 公共包

Monorepo 内可被 `apps/web` 及其他前端包引用的共享代码。

| 包名 | 目录 | 职责 |
|:-----|:-----|:-----|
| `@memoryos/shared` | [`shared/`](./shared/) | 共享 TypeScript 类型、常量、工具函数 |
| `@memoryos/ui` | [`ui/`](./ui/) | 可复用 React UI 组件 |

## 在 web 中引用

```json
// apps/web/package.json
{
  "dependencies": {
    "@memoryos/shared": "workspace:*",
    "@memoryos/ui": "workspace:*"
  }
}
```

```ts
import { APP_NAME } from "@memoryos/shared";
```

## 开发

```bash
# 仓库根目录安装依赖后，workspace 包自动链接
pnpm install
```
