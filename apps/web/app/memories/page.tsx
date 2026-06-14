import type { Metadata } from "next";
import Link from "next/link";

import { MemoryList } from "@/components/memories/memory-list";

export const metadata: Metadata = {
  title: "我的记忆",
};

export default function MemoriesPage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl flex-col px-4 py-6">
      <header className="mb-6 flex shrink-0 items-start justify-between border-b border-zinc-200 pb-4 dark:border-zinc-800">
        <div>
          <h1 className="text-lg font-semibold">我的记忆</h1>
          <p className="mt-1 text-xs text-zinc-500">
            查看与删除系统从对话中抽取的长期记忆（偏好、事实、约束）
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3 text-sm">
          <Link href="/chat" className="text-emerald-600 hover:underline">
            对话
          </Link>
          <Link href="/" className="text-zinc-500 hover:underline">
            首页
          </Link>
        </div>
      </header>
      <MemoryList />
    </div>
  );
}
