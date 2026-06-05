"use client";

import { useChat } from "@ai-sdk/react";
import { useQueryClient } from "@tanstack/react-query";
import { TextStreamChatTransport } from "ai";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatHeader } from "@/components/chat/chat-header";
import { ChatLoading } from "@/components/chat/chat-loading";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { ChatShell } from "@/components/chat/chat-shell";
import { ApiError, apiFetch } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";
import {
  EMPTY_MESSAGES,
  messagesFingerprint,
  toUIMessages,
  type ConversationRead,
} from "@/lib/chat-types";
import { useConversationMessages } from "@/hooks/use-conversation-messages";
import { useMe } from "@/hooks/use-me";

export function MinimalChat() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const conversationId = searchParams.get("conversation_id");

  const [input, setInput] = useState("");
  const [bootstrapping, setBootstrapping] = useState(!conversationId);
  const [error, setError] = useState<string | null>(null);
  const syncedFingerprintRef = useRef("");

  const token = getAccessToken();
  const { data: me, isLoading: meLoading } = useMe(Boolean(token));
  const {
    data: persistedData,
    isLoading: messagesLoading,
    isFetching: messagesFetching,
    isError: messagesError,
    error: messagesQueryError,
  } = useConversationMessages(conversationId);
  const persistedMessages = persistedData ?? EMPTY_MESSAGES;

  const transport = useMemo(
    () =>
      new TextStreamChatTransport({
        api: "/api/chat",
        headers: () => {
          const accessToken = getAccessToken();
          if (!accessToken) {
            return {} as Record<string, string>;
          }
          return { Authorization: `Bearer ${accessToken}` };
        },
        prepareSendMessagesRequest: ({ id, messages }) => ({
          body: {
            id,
            conversation_id: id,
            messages,
          },
        }),
      }),
    [],
  );

  const { messages, sendMessage, status, stop, setMessages } = useChat({
    id: conversationId ?? "pending",
    transport,
    onFinish: () => {
      if (conversationId) {
        void queryClient.invalidateQueries({
          queryKey: chatQueryKeys.messages(conversationId),
        });
      }
    },
    onError: (err) => {
      setError(err.message);
    },
  });

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [router, token]);

  useEffect(() => {
    if (conversationId) {
      setBootstrapping(false);
      return;
    }

    if (meLoading) {
      setBootstrapping(true);
      return;
    }

    if (!me) {
      setBootstrapping(false);
      return;
    }

    let cancelled = false;

    async function createConversation() {
      setBootstrapping(true);
      setError(null);
      try {
        const created = await apiFetch<ConversationRead>(
          "/api/v1/conversations",
          {
            method: "POST",
            body: JSON.stringify({
              user_id: me!.id,
              title: "新对话",
            }),
          },
        );
        const convId = created.data?.id;
        if (!convId || cancelled) {
          return;
        }
        router.replace(`/chat?conversation_id=${convId}`);
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("加载失败");
        }
        setBootstrapping(false);
      }
    }

    void createConversation();

    return () => {
      cancelled = true;
    };
  }, [conversationId, me, meLoading, router]);

  useEffect(() => {
    syncedFingerprintRef.current = "";
  }, [conversationId]);

  useEffect(() => {
    if (status !== "ready" || messagesLoading || messagesFetching) {
      return;
    }

    const fingerprint = messagesFingerprint(persistedMessages);
    if (syncedFingerprintRef.current === fingerprint) {
      return;
    }

    syncedFingerprintRef.current = fingerprint;
    setMessages(toUIMessages(persistedMessages));
  }, [persistedMessages, status, messagesLoading, messagesFetching, setMessages]);

  const isStreaming = status === "submitted" || status === "streaming";
  const loading =
    bootstrapping ||
    (!conversationId && meLoading) ||
    (Boolean(conversationId) && messagesLoading);

  const queryErrorMessage =
    messagesError && messagesQueryError instanceof Error
      ? messagesQueryError.message
      : messagesError
        ? "消息加载失败"
        : null;

  const streamingMessageId =
    isStreaming && messages.at(-1)?.role === "assistant"
      ? (messages.at(-1)?.id ?? null)
      : null;

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !conversationId || isStreaming) {
      return;
    }

    setInput("");
    setError(null);
    await sendMessage({ text });
  }

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
          errorMessage={queryErrorMessage ?? error}
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
