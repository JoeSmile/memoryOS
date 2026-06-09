"use client";

import { useChat } from "@ai-sdk/react";
import { useQueryClient } from "@tanstack/react-query";
import { DefaultChatTransport } from "ai";
import { useRouter, useSearchParams } from "next/navigation";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { flushSync } from "react-dom";

import {
  fetchConversationMessages,
  useConversationMessages,
} from "@/hooks/use-conversation-messages";
import { useMe } from "@/hooks/use-me";
import { ApiError, apiFetch } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";
import {
  EMPTY_MESSAGES,
  getRagSourcesFromUIMessage,
  getTextFromUIMessage,
  messagesFingerprint,
  toUIMessages,
  type ConversationRead,
  type MessageRead,
  type UserRead,
} from "@/lib/chat-types";
import { buildCancelVisiblePayload } from "@/lib/memoryos-upstream";
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
  const resetPersistedSyncFingerprint = useChatStore(
    (state) => state.resetPersistedSyncFingerprint,
  );
  const setStreamingRagSources = useChatStore(
    (state) => state.setStreamingRagSources,
  );
  const commitStreamingRagSources = useChatStore(
    (state) => state.commitStreamingRagSources,
  );
  const hydrateHistoryRagSources = useChatStore(
    (state) => state.hydrateHistoryRagSources,
  );

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
  const [isSending, setIsSending] = useState(false);
  const sendMetaRef = useRef<{
    clientMessageId: string | null;
    regenerate: boolean;
  }>({ clientMessageId: null, regenerate: false });
  const streamIdRef = useRef<string | null>(null);

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: "/api/chat",
        fetch: async (input, init) => {
          streamIdRef.current = null;
          const response = await fetch(input, init);
          const headerStreamId = response.headers.get("X-Stream-Id");
          if (headerStreamId) {
            streamIdRef.current = headerStreamId;
          }
          return response;
        },
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
            client_message_id: sendMetaRef.current.clientMessageId ?? undefined,
            regenerate: sendMetaRef.current.regenerate,
          },
        }),
      }),
    [],
  );

  const clearSendMeta = useCallback(() => {
    sendMetaRef.current = { clientMessageId: null, regenerate: false };
    setIsSending(false);
  }, []);

  const syncPersistedMessages = useCallback(
    async (options?: { retryUntilAssistant?: boolean }) => {
      if (!conversationId) {
        return;
      }

      resetPersistedSyncFingerprint();
      const queryKey = chatQueryKeys.messages(conversationId);
      const maxAttempts = options?.retryUntilAssistant ? 15 : 1;

      for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
        await queryClient.fetchQuery({
          queryKey,
          queryFn: () => fetchConversationMessages(conversationId),
          staleTime: 0,
        });
        if (!options?.retryUntilAssistant) {
          break;
        }
        const rows = queryClient.getQueryData<MessageRead[]>(queryKey) ?? [];
        const last = rows.at(-1);
        if (last?.role === "assistant" || attempt === maxAttempts - 1) {
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 200));
      }

      const rows = queryClient.getQueryData<MessageRead[]>(queryKey) ?? [];
      hydrateHistoryRagSources(rows);
    },
    [
      conversationId,
      queryClient,
      resetPersistedSyncFingerprint,
      hydrateHistoryRagSources,
    ],
  );

  const { messages, sendMessage, status, stop, setMessages } = useChat({
    id: conversationId ?? "pending",
    transport,
    onFinish: () => {
      clearSendMeta();
      void syncPersistedMessages({ retryUntilAssistant: true });
    },
    onError: (err) => {
      clearSendMeta();
      if (conversationId) {
        if (err.name === "AbortError") {
          void syncPersistedMessages({ retryUntilAssistant: true });
        } else {
          void queryClient.invalidateQueries({
            queryKey: chatQueryKeys.messages(conversationId),
          });
        }
      }
      if (err.name !== "AbortError") {
        setError(err.message);
      }
    },
  });

  const messagesRef = useRef(messages);
  messagesRef.current = messages;

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

    const lastLocal = messages.at(-1);
    const lastPersisted = persistedMessages.at(-1);
    if (
      lastLocal?.role === "assistant" &&
      lastPersisted?.role !== "assistant" &&
      getTextFromUIMessage(lastLocal).length > 0
    ) {
      return;
    }

    markPersistedMessagesSynced(fingerprint);
    hydrateHistoryRagSources(persistedMessages);
    setMessages(toUIMessages(persistedMessages));
  }, [
    messages,
    persistedMessages,
    status,
    messagesLoading,
    messagesFetching,
    setMessages,
    shouldSyncPersistedMessages,
    markPersistedMessagesSynced,
    hydrateHistoryRagSources,
  ]);

  const isStreaming = status === "submitted" || status === "streaming";

  useEffect(() => {
    const last = messages.at(-1);
    if (last?.role !== "assistant") {
      if (!isStreaming) {
        setStreamingRagSources(null);
      }
      return;
    }

    const sources = getRagSourcesFromUIMessage(last);
    if (isStreaming) {
      setStreamingRagSources(sources);
      return;
    }

    if (sources) {
      setStreamingRagSources(sources);
    }
    commitStreamingRagSources(last.id);
  }, [
    messages,
    isStreaming,
    setStreamingRagSources,
    commitStreamingRagSources,
  ]);

  useEffect(() => {
    if (messagesLoading || !persistedMessages.length) {
      return;
    }
    hydrateHistoryRagSources(persistedMessages);
  }, [conversationId, messagesLoading, persistedMessages, hydrateHistoryRagSources]);

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
    if (!text || !conversationId || isStreaming || isSending) {
      return;
    }

    sendMetaRef.current = {
      clientMessageId: crypto.randomUUID(),
      regenerate: false,
    };
    setIsSending(true);
    setError(null);
    prepareSend();
    try {
      await sendMessage({ text });
    } catch {
      clearSendMeta();
    }
  }

  async function regenerateLatest() {
    if (!conversationId || isStreaming || isSending) {
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

    sendMetaRef.current = { clientMessageId: null, regenerate: true };
    setIsSending(true);
    setError(null);
    flushSync(() => {
      setMessages((current) => {
        const last = current.at(-1);
        if (last?.role === "assistant") {
          return current.slice(0, -1);
        }
        return current;
      });
    });
    try {
      const pending = sendMessage({ text });
      flushSync(() => {
        setMessages((current) => {
          if (current.length < 2) {
            return current;
          }
          const last = current.at(-1);
          const prev = current.at(-2);
          if (
            last?.role === "user" &&
            prev?.role === "user" &&
            getTextFromUIMessage(last) === getTextFromUIMessage(prev)
          ) {
            return current.slice(0, -1);
          }
          return current;
        });
      });
      await pending;
    } catch {
      clearSendMeta();
    }
  }

  return {
    conversationId,
    messages,
    input,
    setInput,
    isStreaming,
    isSending,
    loading,
    streamingMessageId,
    loadedMessageCount: messages.length,
    errorMessage: queryErrorMessage ?? error,
    handleSubmit,
    regenerateLatest,
    startNewConversation,
    retrySession,
    canRetrySession: Boolean(error) && !conversationId && !isStreaming,
    stop: () => {
      const activeStreamId = streamIdRef.current;
      const lastMessage = messagesRef.current.at(-1);
      const visibleContent =
        lastMessage?.role === "assistant"
          ? getTextFromUIMessage(lastMessage)
          : "";

      if (lastMessage?.role === "assistant") {
        flushSync(() => {
          setMessages((current) => {
            const tail = current.at(-1);
            if (tail?.role !== "assistant") {
              return current;
            }
            return [
              ...current.slice(0, -1),
              {
                ...tail,
                parts: [{ type: "text" as const, text: visibleContent }],
              },
            ];
          });
        });
      }

      const accessToken = getAccessToken();
      if (activeStreamId && accessToken) {
        const cancelVisible = buildCancelVisiblePayload(visibleContent);
        void fetch("/api/chat/cancel", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            stream_id: activeStreamId,
            ...cancelVisible,
          }),
        }).catch(() => {
          // Best-effort cancel when AbortController alone is insufficient.
        });
      }

      stop();
      streamIdRef.current = null;
    },
  };
}
