import type { UIMessage } from "ai";
import { useEffect, useMemo, useRef } from "react";

import { ChatMessage } from "@/components/chat/chat-message";

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
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const latestAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i]?.role === "assistant") {
        return messages[i]?.id ?? null;
      }
    }
    return null;
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessageId]);

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto pb-4">
      {messages.length === 0 ? (
        <p className="text-center text-sm text-zinc-500">{emptyLabel}</p>
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
