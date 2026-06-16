import type { UIMessage } from "ai";
import { useEffect, useMemo, useRef } from "react";

import { ChatMessage } from "@/components/chat/chat-message";
import { ChatThinkingIndicator } from "@/components/chat/chat-thinking-indicator";
import { isDemoUIMessage } from "@/lib/chat-types";

const BOTTOM_THRESHOLD_PX = 80;

/**
 * List-level thinking bubble (not the in-assistant placeholder).
 * - Demo / pre-stream: isSending && !isStreaming
 * - LLM SSE: streaming but assistant row not yet materialized
 * When the streaming assistant bubble exists (even empty), only in-bubble ThinkingPulse shows.
 */
function shouldShowListThinking(
  isSending: boolean,
  isStreaming: boolean,
  lastMessageRole: UIMessage["role"] | undefined,
): boolean {
  if (isSending && !isStreaming) {
    return true;
  }
  return isStreaming && lastMessageRole !== "assistant";
}

type ChatMessageListProps = {
  messages: UIMessage[];
  streamingMessageId?: string | null;
  isStreaming?: boolean;
  isSending?: boolean;
  onRegenerate?: () => void;
  emptyLabel?: string;
  thinkingLabel?: string;
};

export function ChatMessageList({
  messages,
  streamingMessageId = null,
  isStreaming = false,
  isSending = false,
  onRegenerate,
  emptyLabel = "发送一条消息开始分析",
  thinkingLabel = "思考中…",
}: ChatMessageListProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const isNearBottomRef = useRef(true);

  const latestAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i]?.role === "assistant") {
        return messages[i]?.id ?? null;
      }
    }
    return null;
  }, [messages]);

  const lastMessage = messages.at(-1);
  const showThinking = shouldShowListThinking(
    isSending,
    isStreaming,
    lastMessage?.role,
  );

  function updateNearBottom() {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    const distanceFromBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight;
    isNearBottomRef.current = distanceFromBottom <= BOTTOM_THRESHOLD_PX;
  }

  useEffect(() => {
    if (!isNearBottomRef.current) {
      return;
    }
    messagesEndRef.current?.scrollIntoView({
      behavior: isStreaming ? "auto" : "smooth",
    });
  }, [messages, streamingMessageId, isStreaming, showThinking]);

  return (
    <div
      ref={scrollRef}
      onScroll={updateNearBottom}
      className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overscroll-contain pb-4"
    >
      {messages.length === 0 ? (
        <div className="flex min-h-[12rem] flex-col items-center justify-center gap-2 py-12 text-center">
          <p className="text-sm text-zinc-500">{emptyLabel}</p>
          <p className="text-xs text-zinc-400">
            支持连续追问；完整上下文裁剪在后端（EP05）
          </p>
        </div>
      ) : null}

      {messages.map((message) => {
        const messageIsStreaming =
          message.role === "assistant" && message.id === streamingMessageId;
        return (
          <ChatMessage
            key={message.id}
            message={message}
            isStreaming={messageIsStreaming}
            streamingPlaceholderLabel={thinkingLabel}
            showRegenerate={
              !isStreaming &&
              message.role === "assistant" &&
              message.id === latestAssistantId &&
              Boolean(onRegenerate) &&
              !isDemoUIMessage(message)
            }
            onRegenerate={onRegenerate}
          />
        );
      })}

      {showThinking ? <ChatThinkingIndicator label={thinkingLabel} /> : null}

      <div ref={messagesEndRef} />
    </div>
  );
}
