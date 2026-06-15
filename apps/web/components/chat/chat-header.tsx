import Link from "next/link";

import { Wc2022MatchPicker } from "@/components/chat/wc2022-match-picker";
import type { WcMatchBrief } from "@/lib/worldcup-types";

type ChatHeaderProps = {
  title?: string;
  loadedMessageCount?: number;
  pickerDisabled?: boolean;
  onRunDemoAnalysis?: (match: WcMatchBrief, templateId: string) => void;
};

export function ChatHeader({
  title = "2022 世界杯分析",
  loadedMessageCount = 0,
  pickerDisabled = false,
  onRunDemoAnalysis,
}: ChatHeaderProps) {
  return (
    <header className="mb-4 flex shrink-0 flex-col gap-3 border-b border-zinc-200 pb-4 dark:border-zinc-800">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{title}</h1>
          <p className="text-xs text-zinc-500">
            演示模式 · 选阶段、比赛、分析维度后点击「开始分析」
          </p>
          {loadedMessageCount > 0 ? (
            <p className="mt-1 text-xs text-zinc-500">
              {loadedMessageCount} 条消息在会话中
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <Link
            href="/memories"
            className="text-sm text-zinc-600 hover:text-emerald-600 hover:underline dark:text-zinc-400"
          >
            我的记忆
          </Link>
          <Link href="/" className="text-sm text-emerald-600 hover:underline">
            首页
          </Link>
        </div>
      </div>
      <Wc2022MatchPicker
        disabled={pickerDisabled}
        onRunDemoAnalysis={onRunDemoAnalysis}
      />
    </header>
  );
}
