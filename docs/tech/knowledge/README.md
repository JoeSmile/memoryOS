# 技术知识笔记

个人学习沉淀，非项目运行配置。

## 本地排版（不用 AI 烧 token）

1. 安装工作区推荐扩展：命令面板 → **Extensions: Show Recommended Extensions**
2. 写完后 **保存**（已开 `formatOnSave`）或 `Shift+Option+F` 格式化
3. 长文需要目录：**Markdown All in One** → `Create Table of Contents`

| 工具 | 作用 |
|:-----|:-----|
| [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) | 换行、列表、表格周边空行 |
| [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint) | 标题层级、空行、链接等结构告警 |
| [Markdown All in One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) | TOC、列表快捷键、加粗 |

本目录 [`/.prettierrc`](./.prettierrc) 使用 `proseWrap: "preserve"`，**不会**把长段落硬折行；表格 / 代码块照常格式化。  
仓库根目录 `.prettierrc` 仍为 `always`，仅影响其他路径下的 Markdown。

## 索引

- [nextjs15.md](./nextjs15.md) — Next.js 15.5.18 复盘（含 Turbopack 版本表）
- [vite-vs-turbopack.md](./vite-vs-turbopack.md) — Vite 与 Turbopack 对比
