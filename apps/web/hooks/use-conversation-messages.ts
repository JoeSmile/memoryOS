"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { MessageRead } from "@/lib/chat-types";
import { chatQueryKeys } from "@/lib/chat-query-keys";

export async function fetchConversationMessages(
  conversationId: string,
): Promise<MessageRead[]> {
  const res = await apiFetch<MessageRead[]>(
    `/api/v1/conversations/${conversationId}/messages`,
  );
  return res.data ?? [];
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: chatQueryKeys.messages(conversationId ?? ""),
    queryFn: () => fetchConversationMessages(conversationId!),
    enabled: Boolean(conversationId),
  });
}
