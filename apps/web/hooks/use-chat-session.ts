"use client";

import { useChat } from "@ai-sdk/react";
import { useQueryClient } from "@tanstack/react-query";
import { TextStreamChatTransport } from "ai";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo } from "react";

import { useConversationMessages } from "@/hooks/use-conversation-messages";
import { useMe } from "@/hooks/use-me";
import { ApiError, apiFetch } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";
import {
  EMPTY_MESSAGES,
  messagesFingerprint,
  toUIMessages,
  type ConversationRead,
} from "@/lib/chat-types";
import { useChatStore } from "@/stores/chat-store";

export function useChatSession() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const conversationId = searchParams.get("conversation_id");

  const input = useChatStore((state) => state.input);
  const error = useChatStore((state) => state.error);
  const bootstrapping = useChatStore((state) => state.bootstrapping);
  const setInput = useChatStore((state) => state.setInput);
  const setError = useChatStore((state) => state.setError);
  const setBootstrapping = useChatStore((state) => state.setBootstrapping);
  const resetConversationSync = useChatStore(
    (state) => state.resetConversationSync,
  );
  const shouldSyncPersistedMessages = useChatStore(
    (state) => state.shouldSyncPersistedMessages,
  );
  const markPersistedMessagesSynced = useChatStore(
    (state) => state.markPersistedMessagesSynced,
  );
  const prepareSend = useChatStore((state) => state.prepareSend);

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
  }, [conversationId, me, meLoading, router, setBootstrapping, setError]);

  useEffect(() => {
    resetConversationSync();
  }, [conversationId, resetConversationSync]);

  useEffect(() => {
    if (status !== "ready" || messagesLoading || messagesFetching) {
      return;
    }

    const fingerprint = messagesFingerprint(persistedMessages);
    if (!shouldSyncPersistedMessages(fingerprint)) {
      return;
    }

    markPersistedMessagesSynced(fingerprint);
    setMessages(toUIMessages(persistedMessages));
  }, [
    persistedMessages,
    status,
    messagesLoading,
    messagesFetching,
    setMessages,
    shouldSyncPersistedMessages,
    markPersistedMessagesSynced,
  ]);

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

    prepareSend();
    await sendMessage({ text });
  }

  return {
    conversationId,
    messages,
    input,
    setInput,
    isStreaming,
    loading,
    streamingMessageId,
    errorMessage: queryErrorMessage ?? error,
    handleSubmit,
    stop,
  };
}
