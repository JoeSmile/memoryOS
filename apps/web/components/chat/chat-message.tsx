"use client";

import type { UIMessage } from "ai";

import { MessageContent } from "@/components/chat/message-content";
import { RagSourceChipList } from "@/components/chat/rag-source-chip";
import { ToolTimeline } from "@/components/chat/tool-timeline";
import {
  COMPLETION_INTERRUPTED,
  getCompletionStatus,
  getRagSourcesFromUIMessage,
  getTextFromUIMessage,
  getToolStepsFromUIMessage,
} from "@/lib/chat-types";
import { useChatStore } from "@/stores/chat-store";

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
  const storeSources = useChatStore((state) => {
    if (isUser) {
      return null;
    }
    if (isStreaming && state.streamingRagSources?.length) {
      return state.streamingRagSources;
    }
    return state.ragSourcesByMessageId[message.id] ?? null;
  });
  const ragSources =
    getRagSourcesFromUIMessage(message) ?? storeSources ?? null;
  const storeToolSteps = useChatStore((state) => {
    if (isUser) {
      return null;
    }
    if (isStreaming && state.streamingToolSteps?.length) {
      return state.streamingToolSteps;
    }
    return state.toolStepsByMessageId[message.id] ?? null;
  });
  const toolSteps =
    getToolStepsFromUIMessage(message) ?? storeToolSteps ?? null;
  const hasMarkdownRagSources =
    !isUser && !isStreaming && text.includes("## 参考来源");

  return (
    <div
      className={`rounded-xl px-4 py-3 text-sm ${
        isUser
          ? "ml-8 bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
          : "mr-8 border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
      }`}
      data-rag-sources={
        ragSources?.length
          ? "structured"
          : hasMarkdownRagSources
            ? "markdown"
            : undefined
      }
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
      {ragSources ? <RagSourceChipList items={ragSources} /> : null}
      {!isUser ? (
        <ToolTimeline
          message={message}
          steps={toolSteps}
          isStreaming={isStreaming}
        />
      ) : null}
      {!isUser && isStreaming && !text.trim() ? (
        <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
          <span className="inline-flex gap-1" aria-hidden>
            <span
              className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500 [animation-delay:-0.3s]"
            />
            <span
              className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500 [animation-delay:-0.15s]"
            />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500" />
          </span>
          <span className="text-sm">思考中…</span>
        </div>
      ) : (
        <MessageContent
          content={text}
          markdown={!isUser && !isStreaming}
        />
      )}
      {interrupted ? (
        <p className="mt-1 text-xs text-zinc-500" aria-hidden>
          …
        </p>
      ) : null}
    </div>
  );
}
