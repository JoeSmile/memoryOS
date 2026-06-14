"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, deleteMemory, listMemories } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";
import {
  MEMORY_TYPE_LABELS,
  type MemoryRead,
} from "@/lib/memory-types";

function formatWhen(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function MemoryList() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const token = getAccessToken();

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  const {
    data: memories = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: chatQueryKeys.memories,
    queryFn: () => listMemories(),
    enabled: Boolean(token),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMemory,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: chatQueryKeys.memories });
    },
    onError: (err: unknown) => {
      if (err instanceof ApiError) {
        setActionError(err.message);
        return;
      }
      setActionError("delete_failed");
    },
    onSettled: () => {
      setDeletingId(null);
    },
  });

  const handleDelete = async (memory: MemoryRead) => {
    const confirmed = window.confirm(
      `确定删除这条${MEMORY_TYPE_LABELS[memory.memory_type]}记忆？\n\n${memory.content}`,
    );
    if (!confirmed) {
      return;
    }
    setActionError(null);
    setDeletingId(memory.id);
    await deleteMutation.mutateAsync(memory.id);
  };

  if (!token) {
    return (
      <p className="text-sm text-zinc-500">正在跳转到登录页…</p>
    );
  }

  if (isLoading) {
    return (
      <p className="text-sm text-zinc-500">加载记忆中…</p>
    );
  }

  if (isError) {
    const message =
      error instanceof ApiError ? error.message : "load_memories_failed";
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
        <p>加载失败：{message}</p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="mt-2 text-emerald-600 hover:underline"
        >
          重试
        </button>
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          还没有长期记忆
        </p>
        <p className="mt-2 text-sm text-zinc-500">
          对话完成后系统会异步抽取偏好、事实与约束；也可在聊天中继续积累。
        </p>
        <Link
          href="/chat"
          className="mt-4 inline-block text-sm text-emerald-600 hover:underline"
        >
          去对话
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {actionError ? (
        <p className="text-sm text-red-600 dark:text-red-400">
          操作失败：{actionError}
        </p>
      ) : null}
      <ul className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
        {memories.map((memory) => (
          <li
            key={memory.id}
            className="flex flex-col gap-3 p-4 sm:flex-row sm:items-start sm:justify-between"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                  {MEMORY_TYPE_LABELS[memory.memory_type]}
                </span>
                <span>重要度 {(memory.importance * 100).toFixed(0)}%</span>
                <span>更新于 {formatWhen(memory.updated_at)}</span>
              </div>
              <p className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">
                {memory.content}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleDelete(memory)}
              disabled={deletingId === memory.id}
              className="shrink-0 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-red-950/30"
            >
              {deletingId === memory.id ? "删除中…" : "删除"}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
