# MemoryOS 项目计划

> 在 VS Code 安装 [Kanban](https://marketplace.visualstudio.com/items?itemName=mkloubert.vscode-kanban) 插件后打开本文件，可切换为看板视图。  
> 完成任务后将 `- [ ]` 改为 `- [x]` 即可标记完成。

---

🛠 完整技术栈清单
前端技术栈
框架：Next.js 15 + React
语言：TypeScript
样式：TailwindCSS
代码规范：ESLint + Prettier
路由：App Router
状态管理：Zustand
富文本渲染：react-markdown（代码高亮 / 表格 / 引用）
流式通信：前端 ReadableStream / SSE 客户端
工程：路径别名、模块化拆分
后端技术栈
框架：FastAPI（Python）
运行：uvicorn 异步服务
数据模型：Pydantic
网络请求：httpx
LLM 对接：OpenAI SDK、通用大模型调用
鉴权：JWT 登录授权
通信协议：SSE 流式推送
数据库 & 存储
关系型数据库：PostgreSQL
ORM 框架：SQLAlchemy
数据库迁移：Alembic
向量数据库：pgvector
缓存中间件：Redis
文件存储：本地 / 腾讯云 COS
核心 AI 业务技术
大模型应用：Prompt 工程、角色设定、上下文管理
流式对话：SSE 全链路流式输出
RAG 知识库：文档解析、文本切块、Embedding 向量化、相似度召回、重排、溯源引用
Agent 智能体：Function Calling、ReAct 执行逻辑、工具编排、失败重试
记忆体系：短期滑动窗口记忆、长期用户画像记忆、上下文摘要压缩
AI 工作流：节点编排、任务队列、流程状态调度
运维 & 部署 & 工程化
容器化：Docker、Docker Compose、多阶段构建
反向代理：Nginx（SSE 转发、跨域、HTTPS、静态托管）
服务器：腾讯云轻量应用服务器（Ubuntu）
域名与证书：域名解析、SSL 证书配置
CI/CD：GitHub Actions 自动构建 + 自动部署
运维能力：环境变量隔离、日志收集、异常监控、限流风控
开发规范
项目架构：Monorepo 统一仓库架构
目录分层：apps 业务应用 + packages 公共包 + infra 运维配置
Git 规范：分支管理、提交规范、.gitignore 配置



## 迭代概览

| 迭代 | 时间 | 史诗 | 目标 |
|:----:|:-----|:-----|:-----|
| 1 | 第 1-2 周 | EP01 + EP03 | 工程初始化 + 数据存储层搭建 |
| 2 | 第 3 周 | EP02 | 流式对话与多轮会话基础 |
| 3 | 第 4-5 周 | EP04 | RAG 知识库完整闭环 |
| 4 | 第 6 周 | EP05 | Agent 工具调用与智能执行 |
| 5 | 第 7 周 | EP06 + EP07 | 记忆系统 + 工作流 Demo |
| 6 | 第 8 周 | EP08 | 容器化部署 + 线上上线 |
| 7 | 第 9 周 | EP09 | 性能优化 + 安全加固 |
| 8 | 第 10-12 周 | EP10 | 项目打磨 + 面试冲刺 |

---

## EP01 - 项目工程架构初始化

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 1-2 周 |
| **状态** | 待开始 |
| **优先级** | P0 |

### Story 1.1 Monorepo 目录结构

- [x] 创建根目录 `memoryos/` 及 `apps/`、`packages/`、`infra/` 顶层结构
- [x] 创建 `apps/web`（Next.js 前端）与 `apps/api`（FastAPI 后端）子目录
- [x] 创建 `packages/shared`（共享类型/常量）与 `packages/ui`（可选，公共组件）
- [x] 创建 `infra/docker`、`infra/nginx` 占位目录
- [x] 编写根目录 `package.json`（workspace / pnpm-workspace 或 npm workspaces）
- [x] 编写各子包 `README.md` 说明职责与启动方式

### Story 1.2 Git 与开源规范

- [x] 初始化 Git 仓库，配置 `.gitignore`（Node、Python、IDE、`.env`）
- [x] 编写开源版 `README.md`：项目简介、技术栈、快速启动、目录说明
- [x] 添加 `LICENSE`（MIT 或 Apache-2.0）
- [x] 配置 `.editorconfig` 统一缩进与换行
- [x] 添加 `CONTRIBUTING.md` 贡献指南（可选）

### Story 1.3 Next.js 15 前端初始化

- [ ] 使用 `create-next-app` 初始化 Next.js 15（App Router）
- [ ] 配置 TypeScript、`tsconfig.json` 路径别名（`@/`）
- [ ] 集成 TailwindCSS，配置 `tailwind.config` 与全局样式
- [ ] 配置 ESLint + Prettier，添加 `lint` / `format` 脚本
- [ ] 配置环境变量模板 `.env.example`（`NEXT_PUBLIC_API_URL` 等）
- [ ] 创建基础布局：`app/layout.tsx`、`app/page.tsx`、404 页
- [ ] 验证 `pnpm dev` / `npm run dev` 本地可启动

### Story 1.4 FastAPI 后端初始化

- [ ] 创建 Python 虚拟环境，编写 `requirements.txt` / `pyproject.toml`
- [ ] 安装核心依赖：FastAPI、Uvicorn、Pydantic v2、python-dotenv
- [ ] 搭建目录：`app/main.py`、`app/api/`、`app/core/`、`app/models/`
- [ ] 实现健康检查接口 `GET /health`
- [ ] 配置 CORS 中间件（允许前端域名）
- [ ] 配置全局异常处理与统一响应格式
- [ ] 验证 `uvicorn app.main:app --reload` 本地可启动

### Story 1.5 编码与协作规范

- [ ] 制定前端编码规范文档（命名、组件、Hooks、目录约定）
- [ ] 制定后端编码规范文档（路由、Service 层、异常、日志）
- [ ] 配置 Conventional Commits 提交规范（`feat`/`fix`/`docs` 等）
- [ ] 可选：配置 Husky + commitlint 提交校验
- [ ] 可选：配置 pre-commit（Python black/ruff、前端 lint-staged）

---

## EP02 - 流式对话与多轮会话

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 3 周 |
| **状态** | 待开始 |
| **优先级** | P0 |
| **依赖** | EP01、EP03 |

### Story 2.1 聊天基础 UI

- [ ] 设计聊天页路由 `/chat` 及整体布局（侧栏 + 主区域）
- [ ] 实现会话列表组件：新建、选中高亮、删除确认
- [ ] 实现消息列表组件：用户/助手气泡、时间戳、头像
- [ ] 实现输入框组件：多行输入、Enter 发送、Shift+Enter 换行
- [ ] 实现加载状态：骨架屏或打字机动画占位
- [ ] 实现消息列表自动滚动到底部（新消息、流式更新时）
- [ ] 适配移动端基础响应式布局

### Story 2.2 Markdown 渲染

- [ ] 集成 `react-markdown` 或同类库
- [ ] 配置代码块语法高亮（`rehype-highlight` / `shiki`）
- [ ] 支持 GFM：表格、任务列表、删除线
- [ ] 支持引用块、链接、图片预览
- [ ] 处理流式输出时的不完整 Markdown 渲染边界
- [ ] 添加「复制代码」按钮（可选）

### Story 2.3 后端 SSE 流式接口

- [ ] 设计 `POST /api/v1/chat/completions` 流式接口契约
- [ ] 实现 SSE 响应：`text/event-stream`，按 chunk 推送
- [ ] 对接 OpenAI 兼容流式 API（`stream=True`）
- [ ] 处理流式中断：客户端断开时取消上游请求
- [ ] 统一错误码与 SSE 错误事件格式
- [ ] 编写接口文档（OpenAPI / README 片段）

### Story 2.4 前端流式解析

- [ ] 封装 `fetch` + `ReadableStream` 或 `EventSource` 流式客户端
- [ ] 实现 Token 级实时渲染（追加到当前助手消息）
- [ ] 实现「停止生成」按钮，调用 `AbortController.abort()`
- [ ] 处理网络异常、超时、空响应的用户提示
- [ ] 流式结束后持久化完整消息到状态/后端

### Story 2.5 会话与消息数据

- [ ] 定义 Session / Message 前端 TypeScript 类型
- [ ] 对接后端 CRUD：`POST/GET/DELETE /sessions`、`GET/POST /messages`
- [ ] 实现新建会话、切换会话、删除会话
- [ ] 实现历史消息分页或懒加载
- [ ] 会话标题自动生成（首条消息摘要或 LLM 生成）

### Story 2.6 全局状态管理

- [ ] 使用 Zustand 创建 `useChatStore`：sessions、activeSessionId、messages
- [ ] 管理 loading、streaming、error 状态
- [ ] 封装 `sendMessage`、`stopGeneration`、`switchSession` actions
- [ ] 可选：结合 `persist` 中间件缓存最近会话 ID

---

## EP03 - 数据存储层搭建

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 1-2 周（与 EP01 并行） |
| **状态** | 待开始 |
| **优先级** | P0 |

### Story 3.1 PostgreSQL 部署与表设计

- [ ] 本地 Docker 启动 PostgreSQL 15+（`docker-compose.yml`）
- [ ] 设计 `users` 表：id、email、password_hash、nickname、created_at
- [ ] 设计 `sessions` 表：id、user_id、title、model、created_at、updated_at
- [ ] 设计 `messages` 表：id、session_id、role、content、token_count、created_at
- [ ] 设计外键、级联删除策略（删 session 删 messages）
- [ ] 编写 ER 图或 schema 文档到 `docs/database.md`

### Story 3.2 SQLAlchemy + Alembic

- [ ] 配置 SQLAlchemy 2.0 异步引擎（`asyncpg`）
- [ ] 定义 ORM Model：User、Session、Message
- [ ] 初始化 Alembic，`alembic init` 并配置 `env.py`
- [ ] 生成首个迁移脚本并执行 `alembic upgrade head`
- [ ] 编写 Repository 或 Service 层封装 CRUD

### Story 3.3 Redis 缓存

- [ ] Docker 化部署 Redis 7（加入 `docker-compose.yml`）
- [ ] 封装 Redis 客户端连接池（`redis.asyncio`）
- [ ] 实现会话列表缓存（TTL 可配置）
- [ ] 实现流式生成临时缓存（断线重连可选）
- [ ] 实现 JWT 黑名单 / refresh token 存储（可选）

### Story 3.4 用户认证与鉴权

- [ ] 实现用户注册接口：邮箱校验、密码 bcrypt 哈希
- [ ] 实现用户登录接口：签发 access_token + refresh_token
- [ ] 实现 JWT 中间件：Bearer Token 解析与 `user_id` 注入
- [ ] 实现 `GET /me` 当前用户信息接口
- [ ] 保护需鉴权路由（chat、sessions 等）
- [ ] 前端对接：登录页、Token 存储、请求拦截器

### Story 3.5 数据库优化

- [ ] 为 `messages.session_id`、`sessions.user_id` 添加索引
- [ ] 配置连接池参数（pool_size、max_overflow）
- [ ] 关键写操作使用事务（创建 session + 首条 message）
- [ ] 编写基础查询性能测试脚本（可选）

---

## EP04 - RAG 知识库系统

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 4-5 周 |
| **状态** | 待开始 |
| **优先级** | P0 |
| **依赖** | EP02、EP03 |

### Story 4.1 前端文件上传

- [ ] 创建知识库管理页 `/knowledge`
- [ ] 实现拖拽/点击上传组件（PDF、MD、TXT）
- [ ] 实现上传进度条与取消上传
- [ ] 前端文件校验：大小上限、MIME 类型白名单
- [ ] 实现文档列表：名称、状态、大小、上传时间、删除
- [ ] 对接 `POST /api/v1/knowledge/upload` 分片或直传

### Story 4.2 文档解析与清洗

- [ ] 实现 PDF 解析（`pypdf` / `pdfplumber`）
- [ ] 实现 Markdown / 纯文本解析
- [ ] 文本清洗：去多余空白、页眉页脚、乱码过滤
- [ ] 提取文档元数据：标题、页数、字符数
- [ ] 异步任务队列处理大文件（Celery / BackgroundTasks）

### Story 4.3 文本切块策略

- [ ] 实现固定长度切块（chunk_size、overlap 可配置）
- [ ] 实现按段落/标题的层级切块
- [ ] 实现语义切块（按句子嵌入相似度合并，可选）
- [ ] 切块结果持久化：`document_chunks` 表设计
- [ ] 编写切块策略单元测试（样本文档）

### Story 4.4 向量化与 pgvector

- [ ] PostgreSQL 安装 pgvector 扩展
- [ ] 设计 `embeddings` 表：chunk_id、vector、model_name
- [ ] 接入 Embedding API（OpenAI `text-embedding-3-small` 等）
- [ ] 实现批量向量化与入库 pipeline
- [ ] 创建向量索引（IVFFlat / HNSW，按数据量选择）

### Story 4.5 检索与上下文组装

- [ ] 实现查询向量化
- [ ] 实现余弦相似度 TopK 召回
- [ ] 实现 MMR 去重（可选，提升多样性）
- [ ] 按 token 预算截断上下文
- [ ] 封装 `retrieve_context(query, top_k)` 服务方法

### Story 4.6 RAG 对话与溯源

- [ ] 设计 RAG 提示词模板（system + context + question）
- [ ] 对接聊天接口：支持 `knowledge_base_id` 参数
- [ ] 返回答案时附带引用来源（文档名、chunk 片段、页码）
- [ ] 前端展示引用卡片或可折叠来源列表
- [ ] 无相关文档时的兜底回复策略

### Story 4.7 知识库维护

- [ ] 实现文档增量更新（重传覆盖 / 版本号）
- [ ] 删除文档时同步删除 chunks 与 embeddings
- [ ] 切片去重（相同 hash 跳过）
- [ ] 知识库统计接口：文档数、切片数、存储占用

---

## EP05 - LLM Agent 智能工具调度

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 6 周 |
| **状态** | 待开始 |
| **优先级** | P1 |
| **依赖** | EP02、EP04 |

### Story 5.1 工具调用基础设施

- [ ] 定义统一 Tool Schema（name、description、parameters JSON Schema）
- [ ] 实现工具注册表 `ToolRegistry`（注册、查找、列表）
- [ ] 封装 LLM function calling 请求/响应解析
- [ ] 实现工具执行器 `ToolExecutor`（入参校验、调用、结果格式化）
- [ ] 记录工具调用日志（tool_name、args、result、duration）

### Story 5.2 Agent 核心链路

- [ ] 设计 ReAct / Tool-Use 循环：思考 → 选工具 → 执行 → 观测
- [ ] 设置最大迭代次数防止死循环
- [ ] 实现多轮 tool_calls 直到模型输出最终答案
- [ ] 流式推送 Agent 思考过程（可选，提升可观测性）
- [ ] 编写 Agent 集成测试（mock 工具）

### Story 5.3 内置工具开发

- [ ] **网页搜索**：对接 Serper / Tavily / Bing API
- [ ] **数据库查询**：只读 SQL 执行（白名单表、防注入）
- [ ] **知识库检索**：复用 EP04 `retrieve_context`
- [ ] 每个工具编写独立说明文档与示例

### Story 5.4 容错与降级

- [ ] 工具调用超时配置（默认 30s）
- [ ] 失败重试策略（指数退避，最多 3 次）
- [ ] 工具不可用时的降级提示（跳过该工具继续推理）
- [ ] 异常统一捕获并返回用户友好错误

### Story 5.5 模式切换

- [ ] 聊天接口支持 `mode: chat | agent` 参数
- [ ] 前端切换按钮：普通对话 / Agent 模式
- [ ] Agent 模式展示工具调用时间线 UI
- [ ] 两种模式共享会话历史

---

## EP06 - 多层级记忆系统

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 7 周 |
| **状态** | 待开始 |
| **优先级** | P1 |
| **依赖** | EP02、EP03 |

### Story 6.1 短期记忆

- [ ] 实现滑动窗口：保留最近 N 轮对话
- [ ] 实现 Token 计数（tiktoken）与预算上限配置
- [ ] 超预算时从最早消息开始裁剪
- [ ] 系统提示词 + 短期记忆 + 用户问题的拼接策略

### Story 6.2 长期记忆

- [ ] 设计 `memories` 表：user_id、type、content、importance、embedding
- [ ] 对话结束后异步抽取用户偏好/事实（LLM 结构化输出）
- [ ] 构建用户画像摘要（兴趣、职业、常用设置等）
- [ ] 实现长期记忆向量检索，注入 system prompt
- [ ] 前端「我的记忆」管理页（查看、删除）

### Story 6.3 上下文压缩

- [ ] 历史对话超阈值时触发摘要合并
- [ ] 使用 LLM 生成对话摘要替代原始长历史
- [ ] 摘要 + 最近 N 轮原文的混合上下文策略
- [ ] 压缩任务异步执行，不阻塞主对话

### Story 6.4 记忆生命周期

- [ ] 记忆重要性评分与自动更新（新信息覆盖旧矛盾）
- [ ] 定期清理低重要性 / 过期记忆（cron 或定时任务）
- [ ] 用户手动「忘记」某条记忆接口
- [ ] 记忆相关操作审计日志

---

## EP07 - AI 可视化工作流引擎

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 7 周 |
| **状态** | 待开始 |
| **优先级** | P2 |
| **依赖** | EP05 |

### Story 7.1 工作流引擎架构

- [ ] 定义节点类型：Input、LLM、Tool、Condition、Output
- [ ] 定义工作流 DAG 数据结构（JSON Schema）
- [ ] 实现状态机：pending → running → success / failed
- [ ] 接入异步任务队列（Celery / ARQ / FastAPI BackgroundTasks）
- [ ] 工作流定义持久化表设计

### Story 7.2 简历分析 Demo

- [ ] 节点1：PDF/文本输入 → 简历解析
- [ ] 节点2：LLM 技能提取 → 结构化 JSON
- [ ] 节点3：岗位 JD 输入 → 匹配度分析
- [ ] 节点4：输出匹配报告（技能缺口、建议）
- [ ] 编写端到端 Demo 脚本与样例数据

### Story 7.3 执行可视化

- [ ] 前端工作流画布（React Flow 或简易步骤条）
- [ ] 实时展示当前执行节点与高亮
- [ ] 每个节点输入/输出日志可展开查看
- [ ] 工作流历史列表与重新执行

---

## EP08 - 工程化与腾讯云部署

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 8 周 |
| **状态** | 待开始 |
| **优先级** | P0 |
| **依赖** | EP01–EP07 核心功能 |

### Story 8.1 Docker 镜像

- [ ] 编写 `apps/api/Dockerfile`（多阶段：builder + slim runtime）
- [ ] 编写 `apps/web/Dockerfile`（Next.js standalone 输出）
- [ ] 优化镜像体积：非 root 用户、.dockerignore
- [ ] 本地 `docker build` 验证镜像可运行

### Story 8.2 Docker Compose 本地全栈

- [ ] 编写根目录 `docker-compose.yml`：web、api、postgres、redis、nginx
- [ ] 配置服务依赖与健康检查 `depends_on`
- [ ] 环境变量通过 `.env` 注入，提供 `.env.production.example`
- [ ] 一键启动文档：`docker compose up -d`

### Story 8.3 Nginx 反向代理

- [ ] 配置 upstream：前端静态、API 服务
- [ ] SSE 专用配置：`proxy_buffering off`、`proxy_read_timeout`
- [ ] CORS 与 HTTPS 跳转规则
- [ ] 静态资源缓存策略（`_next/static`）

### Story 8.4 腾讯云服务器

- [ ] 购买/初始化轻量应用服务器（Ubuntu 22.04）
- [ ] 安装 Docker、Docker Compose
- [ ] 配置防火墙：80、443、22 端口
- [ ] 配置 SSH 密钥登录，禁用密码登录（推荐）

### Story 8.5 线上数据服务

- [ ] 部署线上 PostgreSQL（云数据库或容器）
- [ ] 部署线上 Redis
- [ ] 执行生产环境 Alembic 迁移
- [ ] 分环境配置：`development` / `staging` / `production`

### Story 8.6 域名与 HTTPS

- [ ] 域名解析 A 记录指向服务器 IP
- [ ] 使用 Certbot 或腾讯云 SSL 申请证书
- [ ] Nginx 配置 443 与 HTTP → HTTPS 重定向
- [ ] 验证全站 HTTPS 与 API 可访问

### Story 8.7 CI/CD

- [ ] 编写 GitHub Actions workflow：lint → test → build → push image
- [ ] 配置 Secrets：服务器 SSH、镜像仓库、API Keys
- [ ] 实现 main 分支自动部署到腾讯云（SSH deploy 或 webhook）
- [ ] 添加部署状态 Badge 到 README

---

## EP09 - 性能优化与安全加固

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 9 周 |
| **状态** | 待开始 |
| **优先级** | P1 |
| **依赖** | EP08 已上线 |

### Story 9.1 上下文工程安全

- [ ] 实现提示词注入检测规则（敏感模式、角色劫持）
- [ ] 系统提示词加固：明确边界、拒绝越权指令
- [ ] RAG 场景过滤检索内容中的恶意指令
- [ ] 用户输入长度与特殊字符限制

### Story 9.2 性能优化

- [ ] 首包耗时优化：连接复用、模型预热（可选）
- [ ] 实现 LLM 响应缓存（相同问题 hash，TTL）
- [ ] Embedding 结果缓存，避免重复计算
- [ ] Token 用量统计与成本告警阈值
- [ ] 数据库慢查询分析与索引补充

### Story 9.3 架构文档梳理

- [ ] 绘制整体系统架构图（C4 Context / Container）
- [ ] 梳理 RAG 流水线时序图
- [ ] 梳理 Agent 工具调用时序图
- [ ] 梳理记忆系统数据流图
- [ ] 文档归档至 `docs/architecture/`

### Story 9.4 限流与审计

- [ ] 接口限流：按 IP / 用户 ID（Redis 滑动窗口）
- [ ] 防刷：注册、登录、发送消息频率限制
- [ ] 对话用量统计仪表盘（日/月 Token、请求数）
- [ ] 操作审计日志：登录、删文档、删会话等

### Story 9.5 全链路降级

- [ ] LLM 不可用 → 返回友好提示 + 重试建议
- [ ] 向量库不可用 → 降级为关键词检索或纯 LLM
- [ ] Redis 不可用 → 降级直连 DB，记录告警
- [ ] 编写降级策略文档与演练 checklist

---

## EP10 - 项目打磨与面试冲刺

| 属性 | 值 |
|:-----|:---|
| **时间** | 第 10-12 周 |
| **状态** | 待开始 |
| **优先级** | P0 |
| **依赖** | EP01–EP09 |

### Story 10.1 前端体验打磨

- [ ] 消息发送失败重试按钮
- [ ] 对话收藏 / 置顶功能
- [ ] 对话导出 Markdown / JSON
- [ ] 知识库权限：私有 / 公开（按用户）
- [ ] 深色模式（可选）
- [ ] 统一 Loading、Empty、Error 状态组件

### Story 10.2 多模型路由

- [ ] 抽象 `LLMProvider` 接口（OpenAI、DeepSeek、本地 Ollama）
- [ ] 配置化模型列表：名称、endpoint、api_key 环境变量
- [ ] 实现模型自动降级（主模型失败切换备用）
- [ ] 前端模型选择下拉框

### Story 10.3 压测与 Bug 修复

- [ ] 使用 k6 / locust 对核心接口压测
- [ ] 修复压测与线上反馈的 BUG 清单
- [ ] 统一 UI 间距、字体、配色规范
- [ ] 跨浏览器兼容性冒烟测试

### Story 10.4 项目文档与图示

- [ ] 绘制业务流程图（用户注册 → 对话 → RAG → Agent）
- [ ] 绘制数据流转图（上传 → 切块 → 向量 → 检索）
- [ ] 整理 `docs/technical-challenges.md`：难点 + 方案 + 业务价值
- [ ] 完善 README：截图、Demo 链接、架构说明

### Story 10.5 面试材料

- [ ] 整理 RAG 高频面试题 + 本项目标准答案
- [ ] 整理 Agent / Function Calling 高频面试题 + 答案
- [ ] 整理记忆系统 / 上下文工程面试题 + 答案
- [ ] 改写简历项目描述：STAR 法则、量化结果、技术关键词
- [ ] 准备 3 分钟 / 5 分钟项目口述稿

---

## 使用说明

1. **看板视图**：VS Code 安装 Kanban 插件 → 打开本文件 → 命令面板选择「Kanban: Open Board」。
2. **标记完成**：将对应行的 `- [ ]` 改为 `- [x]`。
3. **迭代节奏**：按「迭代概览」表顺序推进；EP01 与 EP03 可并行，EP07 可在 EP06 之后按需裁剪。
4. **优先级**：P0 为阻塞项，P1 为核心增强，P2 为加分项（时间紧可延后 EP07）。
    