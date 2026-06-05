"use client";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatHeader } from "@/components/chat/chat-header";
import { ChatLoading } from "@/components/chat/chat-loading";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { ChatShell } from "@/components/chat/chat-shell";
import { useChatSession } from "@/hooks/use-chat-session";

export function MinimalChat() {
  const {
    conversationId,
    messages,
    input,
    setInput,
    isStreaming,
    loading,
    streamingMessageId,
    errorMessage,
    handleSubmit,
    stop,
  } = useChatSession();

  if (loading) {
    return <ChatLoading />;
  }

  return (
    <ChatShell
      header={<ChatHeader />}
      footer={
        <ChatComposer
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          isStreaming={isStreaming}
          onStop={() => stop()}
          disabled={!conversationId}
          errorMessage={errorMessage}
        />
      }
    >
      <ChatMessageList
        messages={messages}
        streamingMessageId={streamingMessageId}
      />
    </ChatShell>
  );
}
