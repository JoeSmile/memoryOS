"use client";

import { formatTokenCount } from "@/lib/format-token-count";
import { useMyUsage } from "@/hooks/use-my-usage";

type TokenUsageButtonProps = {
  className?: string;
};

export function TokenUsageButton({ className }: TokenUsageButtonProps) {
  const { data, isLoading, isFetching, isError, refetch } = useMyUsage();

  const label = (() => {
    if (isLoading && !data) {
      return "Token …";
    }
    if (isError || !data) {
      return "Token —";
    }
    const used = formatTokenCount(data.total_tokens);
    if (data.quota_enabled && data.daily_quota != null) {
      const limit = formatTokenCount(data.daily_quota);
      return `Token ${used} / ${limit}`;
    }
    return `Token ${used}`;
  })();

  return (
    <button
      type="button"
      onClick={() => void refetch()}
      disabled={isFetching}
      className={
        className ??
        "rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
      }
      title="今日 Token 用量（点击刷新）"
      aria-label="今日 Token 用量"
      data-testid="token-usage-button"
    >
      {isFetching && data ? `${label} ↻` : label}
    </button>
  );
}
