import type { UIMessage } from "ai";

import { getTextFromUIMessage } from "@/lib/chat-types";

type ChatMessageProps = {
  message: UIMessage;
  isStreaming?: boolean;
};

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`rounded-xl px-4 py-3 text-sm ${
        isUser
          ? "ml-8 bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
          : "mr-8 border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
      }`}
    >
      <p className="mb-1 text-xs font-medium uppercase tracking-wide opacity-60">
        {isUser ? "你" : "助手"}
        {!isUser && isStreaming ? " · 生成中" : ""}
      </p>
      <p className="whitespace-pre-wrap">{getTextFromUIMessage(message)}</p>
    </div>
  );
}
