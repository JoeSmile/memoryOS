"use client";

import { useChat } from "@ai-sdk/react";
import { useQueryClient } from "@tanstack/react-query";
import { TextStreamChatTransport } from "ai";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo } from "react";

import { useConversationMessages } from "@/hooks/use-conversation-messages";
import { useMe } from "@/hooks/use-me";
import { ApiError, apiFetch } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";
import {
  EMPTY_MESSAGES,
  getTextFromUIMessage,
  messagesFingerprint,
  toUIMessages,
  type ConversationRead,
  type UserRead,
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
  const {
    data: me,
    isLoading: meLoading,
    isError: meError,
    error: meQueryError,
    refetch: refetchMe,
  } = useMe(Boolean(token));
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

  const createConversationRecord = useCallback(
    async (title: string, user: UserRead): Promise<string | null> => {
      const created = await apiFetch<ConversationRead>("/api/v1/conversations", {
        method: "POST",
        body: JSON.stringify({
          user_id: user.id,
          title,
        }),
      });

      void queryClient.invalidateQueries({
        queryKey: chatQueryKeys.myConversations,
      });

      return created.data?.id ?? null;
    },
    [queryClient],
  );

  const bootstrapConversation = useCallback(
    async (user: UserRead) => {
      setBootstrapping(true);
      setError(null);
      try {
        const list = await apiFetch<ConversationRead[]>(
          "/api/v1/conversations/me",
        );
        const latestId = list.data?.[0]?.id;
        if (latestId) {
          router.replace(`/chat?conversation_id=${latestId}`);
          return;
        }

        const convId = await createConversationRecord("新对话", user);
        if (convId) {
          router.replace(`/chat?conversation_id=${convId}`);
        } else {
          setError("创建对话失败");
          setBootstrapping(false);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("加载失败");
        }
        setBootstrapping(false);
      }
    },
    [
      router,
      setBootstrapping,
      setError,
      createConversationRecord,
    ],
  );

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
      if (meError) {
        const msg =
          meQueryError instanceof Error
            ? meQueryError.message
            : "登录信息加载失败";
        setError(msg);
      }
      return;
    }

    void bootstrapConversation(me);
  }, [
    conversationId,
    me,
    meLoading,
    meError,
    meQueryError,
    setBootstrapping,
    setError,
    bootstrapConversation,
  ]);

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

  const startNewConversation = useCallback(async () => {
    if (isStreaming) {
      return;
    }

    let activeMe = me;
    if (!activeMe) {
      const result = await refetchMe();
      activeMe = result.data;
    }
    if (!activeMe) {
      setError("登录信息加载失败，请重试或重新登录");
      return;
    }

    setBootstrapping(true);
    setError(null);
    setMessages([]);
    resetConversationSync();

    try {
      const convId = await createConversationRecord("新分析", activeMe);
      if (convId) {
        router.replace(`/chat?conversation_id=${convId}`);
      } else {
        setError("新建分析失败");
        setBootstrapping(false);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("新建分析失败");
      }
      setBootstrapping(false);
    }
  }, [
    me,
    isStreaming,
    refetchMe,
    setBootstrapping,
    setError,
    setMessages,
    resetConversationSync,
    createConversationRecord,
    router,
  ]);

  const retrySession = useCallback(async () => {
    if (isStreaming || conversationId) {
      return;
    }

    setError(null);
    const result = await refetchMe();
    const activeMe = result.data ?? me;
    if (!activeMe) {
      setError("登录信息加载失败，请重试或重新登录");
      return;
    }

    await bootstrapConversation(activeMe);
  }, [
    isStreaming,
    conversationId,
    refetchMe,
    me,
    setError,
    bootstrapConversation,
  ]);

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

  async function regenerateLatest() {
    if (!conversationId || isStreaming) {
      return;
    }

    const lastUserMessage = [...messages].reverse().find(
      (message) => message.role === "user",
    );
    if (!lastUserMessage) {
      return;
    }

    const text = getTextFromUIMessage(lastUserMessage).trim();
    if (!text) {
      return;
    }

    setError(null);
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
    loadedMessageCount: messages.length,
    errorMessage: queryErrorMessage ?? error,
    handleSubmit,
    regenerateLatest,
    startNewConversation,
    retrySession,
    canRetrySession: Boolean(error) && !conversationId && !isStreaming,
    stop,
  };
}
