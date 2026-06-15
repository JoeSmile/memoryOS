"use client";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatHeader } from "@/components/chat/chat-header";
import { ChatLoading } from "@/components/chat/chat-loading";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { ChatShell } from "@/components/chat/chat-shell";
import { useChatSession } from "@/hooks/use-chat-session";

export function MinimalChat() {
  const {
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
    appendDemoTurn,
    retrySession,
    canRetrySession,
    canCompose,
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
          pickerDisabled={isStreaming || isSending}
          onRunDemoAnalysis={(match, templateId) =>
            void appendDemoTurn(match.id, templateId)
          }
        />
      }
      footer={
        <ChatComposer
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          isStreaming={isStreaming}
          onStop={() => stop()}
          disabled={!canCompose}
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
        isSending={isSending}
        thinkingLabel="正在生成分析…"
        emptyLabel="选择阶段、比赛与分析维度后点击「开始分析」"
        onRegenerate={() => void regenerateLatest()}
      />
    </ChatShell>
  );
}
