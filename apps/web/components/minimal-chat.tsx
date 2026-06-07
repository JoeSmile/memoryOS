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
    isSending,
    loading,
    streamingMessageId,
    loadedMessageCount,
    errorMessage,
    handleSubmit,
    regenerateLatest,
    startNewConversation,
    retrySession,
    canRetrySession,
    stop,
  } = useChatSession();

  if (loading) {
    return <ChatLoading />;
  }

  return (
    <ChatShell
      header={
        <ChatHeader
          loadedMessageCount={loadedMessageCount}
          onNewConversation={() => void startNewConversation()}
          newConversationDisabled={isStreaming || loading}
        />
      }
      footer={
        <ChatComposer
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          isStreaming={isStreaming}
          onStop={() => stop()}
          disabled={!conversationId || isSending}
          errorMessage={errorMessage}
          onRetry={
            canRetrySession ? () => void retrySession() : undefined
          }
        />
      }
    >
      <ChatMessageList
        messages={messages}
        streamingMessageId={streamingMessageId}
        isStreaming={isStreaming}
        onRegenerate={() => void regenerateLatest()}
      />
    </ChatShell>
  );
}
