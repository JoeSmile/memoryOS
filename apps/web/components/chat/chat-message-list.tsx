import type { UIMessage } from "ai";
import { useEffect, useRef } from "react";

import { ChatMessage } from "@/components/chat/chat-message";

type ChatMessageListProps = {
  messages: UIMessage[];
  streamingMessageId?: string | null;
  emptyLabel?: string;
};

export function ChatMessageList({
  messages,
  streamingMessageId = null,
  emptyLabel = "发送一条消息开始分析",
}: ChatMessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

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
        />
      ))}

      <div ref={messagesEndRef} />
    </div>
  );
}
