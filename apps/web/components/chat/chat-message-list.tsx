import type { UIMessage } from "ai";
import { useEffect, useMemo, useRef } from "react";

import { ChatMessage } from "@/components/chat/chat-message";

const BOTTOM_THRESHOLD_PX = 80;

type ChatMessageListProps = {
  messages: UIMessage[];
  streamingMessageId?: string | null;
  isStreaming?: boolean;
  onRegenerate?: () => void;
  emptyLabel?: string;
};

export function ChatMessageList({
  messages,
  streamingMessageId = null,
  isStreaming = false,
  onRegenerate,
  emptyLabel = "发送一条消息开始分析",
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
  }, [messages, streamingMessageId, isStreaming]);

  return (
    <div
      ref={scrollRef}
      onScroll={updateNearBottom}
      className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-4"
    >
      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 py-12 text-center">
          <p className="text-sm text-zinc-500">{emptyLabel}</p>
          <p className="text-xs text-zinc-400">
            支持连续追问；完整上下文裁剪在后端（EP05）
          </p>
        </div>
      ) : null}

      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          message={message}
          isStreaming={
            message.role === "assistant" && message.id === streamingMessageId
          }
          showRegenerate={
            !isStreaming &&
            message.role === "assistant" &&
            message.id === latestAssistantId &&
            Boolean(onRegenerate)
          }
          onRegenerate={onRegenerate}
        />
      ))}

      <div ref={messagesEndRef} />
    </div>
  );
}
