"use client";

import { useChat } from "@ai-sdk/react";
import { useQueryClient } from "@tanstack/react-query";
import { TextStreamChatTransport } from "ai";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

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
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

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
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-zinc-500">
        加载对话…
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-4 py-6">
      <header className="mb-4 flex items-center justify-between border-b border-zinc-200 pb-4 dark:border-zinc-800">
        <div>
          <h1 className="text-lg font-semibold">对话</h1>
          <p className="text-xs text-zinc-500">
            AI SDK + React Query（BFF `/api/chat`）
          </p>
        </div>
        <Link href="/" className="text-sm text-emerald-600 hover:underline">
          首页
        </Link>
      </header>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto pb-4">
        {messages.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">
            发送一条消息开始对话
          </p>
        ) : null}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`rounded-xl px-4 py-3 text-sm ${
              message.role === "user"
                ? "ml-8 bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                : "mr-8 border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
            }`}
          >
            <p className="mb-1 text-xs font-medium uppercase tracking-wide opacity-60">
              {message.role === "user" ? "你" : "助手"}
              {isStreaming &&
              message.role === "assistant" &&
              message.id === messages.at(-1)?.id
                ? " · 生成中"
                : ""}
            </p>
            <p className="whitespace-pre-wrap">
              {message.parts
                .filter((part) => part.type === "text")
                .map((part) => part.text)
                .join("")}
            </p>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {queryErrorMessage ?? error ? (
        <p className="mb-2 text-sm text-red-600 dark:text-red-400" role="alert">
          {queryErrorMessage ?? error}
        </p>
      ) : null}

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入消息…"
          disabled={isStreaming || !conversationId}
          className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={() => stop()}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            停止
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim() || !conversationId}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            发送
          </button>
        )}
      </form>
    </div>
  );
}
