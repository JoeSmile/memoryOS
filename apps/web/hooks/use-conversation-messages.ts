"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { MessageRead } from "@/lib/chat-types";
import { chatQueryKeys } from "@/lib/chat-query-keys";

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: chatQueryKeys.messages(conversationId ?? ""),
    queryFn: async () => {
      const res = await apiFetch<MessageRead[]>(
        `/api/v1/conversations/${conversationId}/messages`,
      );
      return res.data ?? [];
    },
    enabled: Boolean(conversationId),
  });
}
