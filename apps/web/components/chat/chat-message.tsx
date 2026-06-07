import type { UIMessage } from "ai";

import { MessageContent } from "@/components/chat/message-content";
import {
  COMPLETION_INTERRUPTED,
  getCompletionStatus,
  getTextFromUIMessage,
} from "@/lib/chat-types";

type ChatMessageProps = {
  message: UIMessage;
  isStreaming?: boolean;
  showRegenerate?: boolean;
  onRegenerate?: () => void;
};

export function ChatMessage({
  message,
  isStreaming = false,
  showRegenerate = false,
  onRegenerate,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const text = getTextFromUIMessage(message);
  const interrupted =
    !isUser &&
    !isStreaming &&
    getCompletionStatus(message) === COMPLETION_INTERRUPTED;

  return (
    <div
      className={`rounded-xl px-4 py-3 text-sm ${
        isUser
          ? "ml-8 bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
          : "mr-8 border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
      }`}
    >
      <div className="mb-1 flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide opacity-60">
          {isUser ? "你" : "助手"}
          {!isUser && isStreaming ? " · 生成中" : ""}
          {interrupted ? " · 已中断" : ""}
        </p>
        {showRegenerate && onRegenerate ? (
          <button
            type="button"
            onClick={onRegenerate}
            className="text-xs text-emerald-600 hover:underline dark:text-emerald-400"
          >
            重新生成
          </button>
        ) : null}
      </div>
      <MessageContent
        content={text}
        markdown={!isUser && !isStreaming}
      />
      {interrupted ? (
        <p className="mt-1 text-xs text-zinc-500" aria-hidden>
          …
        </p>
      ) : null}
    </div>
  );
}
