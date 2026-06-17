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
import { resolveApiErrorMessage } from "@/lib/api-error-messages";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";
import {
  EMPTY_MESSAGES,
  getRagSourcesFromUIMessage,
  getTextFromUIMessage,
  getToolStepsFromUIMessage,
  messagesFingerprint,
  toUIMessages,
  type ConversationRead,
  type MessageRead,
  type UserRead,
} from "@/lib/chat-types";
import { buildCancelVisiblePayload } from "@/lib/memoryos-upstream";
import { useChatStore } from "@/stores/chat-store";

const DEMO_SESSION_TITLE = "2022世界杯分析";

function formatClientError(err: unknown): string {
  if (err instanceof ApiError) {
    return resolveApiErrorMessage(err.code, err.message, err.data);
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "请求失败";
}

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
  const setStreamingToolSteps = useChatStore(
    (state) => state.setStreamingToolSteps,
  );
  const commitStreamingToolSteps = useChatStore(
    (state) => state.commitStreamingToolSteps,
  );
  const hydrateHistoryToolSteps = useChatStore(
    (state) => state.hydrateHistoryToolSteps,
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

  const syncPersistedMessagesRef = useRef<
    | ((options?: {
        retryUntilAssistant?: boolean;
        replaceLocal?: boolean;
      }) => Promise<void>)
    | null
  >(null);

  const { messages, sendMessage, status, stop, setMessages } = useChat({
    id: conversationId ?? "pending",
    transport,
    onFinish: () => {
      clearSendMeta();
      void queryClient.invalidateQueries({ queryKey: chatQueryKeys.myUsage });
      void syncPersistedMessagesRef.current?.({
        retryUntilAssistant: true,
        replaceLocal: true,
      });
    },
    onError: (err) => {
      clearSendMeta();
      if (conversationId) {
        if (err.name === "AbortError") {
          void syncPersistedMessagesRef.current?.({
            retryUntilAssistant: true,
            replaceLocal: true,
          });
        } else {
          void queryClient.invalidateQueries({
            queryKey: chatQueryKeys.messages(conversationId),
          });
        }
      }
      if (err.name !== "AbortError") {
        setError(formatClientError(err));
      }
    },
  });

  const syncPersistedMessages = useCallback(
    async (options?: {
      retryUntilAssistant?: boolean;
      replaceLocal?: boolean;
    }) => {
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
      hydrateHistoryToolSteps(rows);
      if (options?.replaceLocal) {
        markPersistedMessagesSynced(messagesFingerprint(rows));
        setMessages(toUIMessages(rows));
      }
    },
    [
      conversationId,
      queryClient,
      resetPersistedSyncFingerprint,
      hydrateHistoryRagSources,
      hydrateHistoryToolSteps,
      markPersistedMessagesSynced,
      setMessages,
    ],
  );

  syncPersistedMessagesRef.current = syncPersistedMessages;

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
        const demoConvs =
          list.data?.filter((item) => item.title === DEMO_SESSION_TITLE) ?? [];
        const demoConv =
          demoConvs.length === 0
            ? null
            : demoConvs.reduce<ConversationRead | null>((latest, item) => {
                if (!latest) {
                  return item;
                }
                const itemTs = item.updated_at ?? "";
                const latestTs = latest.updated_at ?? "";
                return itemTs > latestTs ? item : latest;
              }, null);
        if (demoConv) {
          router.replace(`/chat?conversation_id=${demoConv.id}`);
          return;
        }

        const convId = await createConversationRecord(DEMO_SESSION_TITLE, user);
        if (convId) {
          router.replace(`/chat?conversation_id=${convId}`);
        } else {
          setError("创建对话失败");
          setBootstrapping(false);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setError(formatClientError(err));
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
    clearSendMeta();
  }, [conversationId, clearSendMeta]);

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
    hydrateHistoryToolSteps(persistedMessages);
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
    hydrateHistoryToolSteps,
  ]);

  const isStreaming = status === "submitted" || status === "streaming";

  useEffect(() => {
    const last = messages.at(-1);
    if (last?.role !== "assistant") {
      if (!isStreaming) {
        setStreamingRagSources(null);
        setStreamingToolSteps(null);
      }
      return;
    }

    const sources = getRagSourcesFromUIMessage(last);
    const toolSteps = getToolStepsFromUIMessage(last);
    if (isStreaming) {
      setStreamingRagSources(sources);
      setStreamingToolSteps(toolSteps);
      return;
    }

    if (sources) {
      setStreamingRagSources(sources);
    }
    if (toolSteps) {
      setStreamingToolSteps(toolSteps);
    }
    commitStreamingRagSources(last.id);
    commitStreamingToolSteps(last.id);
  }, [
    messages,
    isStreaming,
    setStreamingRagSources,
    commitStreamingRagSources,
    setStreamingToolSteps,
    commitStreamingToolSteps,
  ]);

  useEffect(() => {
    if (messagesLoading || !persistedMessages.length) {
      return;
    }
    hydrateHistoryRagSources(persistedMessages);
    hydrateHistoryToolSteps(persistedMessages);
  }, [
    conversationId,
    messagesLoading,
    persistedMessages,
    hydrateHistoryRagSources,
    hydrateHistoryToolSteps,
  ]);

  const appendDemoTurn = useCallback(
    async (matchId: string, templateId: string) => {
      if (!conversationId || isStreaming || isSending) {
        return;
      }

      setIsSending(true);
      setError(null);
      try {
        await apiFetch(`/api/v1/conversations/${conversationId}/demo-turn`, {
          method: "POST",
          body: JSON.stringify({
            match_id: matchId,
            template_id: templateId,
          }),
        });
        resetPersistedSyncFingerprint();
        const rows = await queryClient.fetchQuery({
          queryKey: chatQueryKeys.messages(conversationId),
          queryFn: () => fetchConversationMessages(conversationId),
          staleTime: 0,
        });
        hydrateHistoryRagSources(rows);
        hydrateHistoryToolSteps(rows);
        markPersistedMessagesSynced(messagesFingerprint(rows));
        setMessages(toUIMessages(rows));
      } catch (err) {
        if (err instanceof ApiError) {
          setError(formatClientError(err));
        } else {
          setError("演示分析写入失败");
        }
      } finally {
        setIsSending(false);
      }
    },
    [
      conversationId,
      isStreaming,
      isSending,
      setError,
      queryClient,
      resetPersistedSyncFingerprint,
      hydrateHistoryRagSources,
      hydrateHistoryToolSteps,
      markPersistedMessagesSynced,
      setMessages,
    ],
  );

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

  const awaitingConversation =
    Boolean(token) &&
    !conversationId &&
    !meLoading &&
    Boolean(me) &&
    !meError &&
    !error;

  const loading =
    bootstrapping ||
    (!conversationId && meLoading) ||
    awaitingConversation ||
    (Boolean(conversationId) && messagesLoading);

  const canCompose =
    Boolean(conversationId) && !isStreaming && !isSending && !loading;

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

    setIsSending(true);
    setError(null);
    try {
      await syncPersistedMessages({ replaceLocal: true });

      const rows =
        queryClient.getQueryData<MessageRead[]>(
          chatQueryKeys.messages(conversationId),
        ) ?? [];
      const lastRow = rows.at(-1);
      if (lastRow?.role !== "assistant") {
        clearSendMeta();
        return;
      }

      const lastUserRow = [...rows].reverse().find((row) => row.role === "user");
      const text = lastUserRow?.content.trim() ?? "";
      if (!text) {
        clearSendMeta();
        return;
      }

      sendMetaRef.current = { clientMessageId: null, regenerate: true };
      flushSync(() => {
        setMessages((current) => {
          const last = current.at(-1);
          if (last?.role === "assistant") {
            return current.slice(0, -1);
          }
          return current;
        });
      });

      const tail = messagesRef.current.at(-1);
      if (tail?.role !== "user") {
        setError("重新生成失败：会话末尾不是用户消息");
        clearSendMeta();
        return;
      }

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
    canCompose,
    streamingMessageId,
    loadedMessageCount: messages.length,
    errorMessage: queryErrorMessage ?? error,
    handleSubmit,
    regenerateLatest,
    appendDemoTurn,
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
