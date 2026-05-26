import Link from "next/link";
import { APP_NAME } from "@memoryos/shared";

const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <span className="text-lg font-semibold tracking-tight">
            {APP_NAME}
          </span>
          <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            EP01 · Story 1.3
          </span>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center gap-8 px-6 py-16">
        <section className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            AI 记忆与知识平台
          </h1>
          <p className="max-w-2xl text-lg text-zinc-600 dark:text-zinc-400">
            流式对话 · RAG 知识库 · Agent 工具调度 · 多层级记忆。前端基于
            Next.js 15 + TailwindCSS，已接入 Monorepo 共享包。
          </p>
        </section>

        <section className="grid gap-4 sm:grid-cols-2">
          <Card
            title="技术栈"
            items={[
              "Next.js 15",
              "TypeScript",
              "TailwindCSS v4",
              "Zustand（EP02）",
            ]}
          />
          <Card
            title="环境"
            items={[`API: ${apiUrl}`, "复制 .env.example → .env.local"]}
          />
        </section>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/register"
            className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            注册
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-zinc-300 px-5 py-2.5 text-sm font-medium transition hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            登录
          </Link>
          <Link
            href="/chat"
            className="rounded-lg border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-500 transition hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            进入对话（EP02）
          </Link>
          <a
            href="https://github.com"
            className="rounded-lg border border-zinc-300 px-5 py-2.5 text-sm font-medium transition hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
            target="_blank"
            rel="noopener noreferrer"
          >
            项目文档
          </a>
        </div>
      </main>

      <footer className="border-t border-zinc-200 px-6 py-4 text-center text-sm text-zinc-500 dark:border-zinc-800">
        MemoryOS Monorepo · apps/web
      </footer>
    </div>
  );
}

function Card({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-zinc-200 p-5 dark:border-zinc-800">
      <h2 className="mb-3 font-semibold">{title}</h2>
      <ul className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
