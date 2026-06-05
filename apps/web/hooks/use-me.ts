"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { UserRead } from "@/lib/chat-types";
import { chatQueryKeys } from "@/lib/chat-query-keys";

export function useMe(enabled = true) {
  return useQuery({
    queryKey: chatQueryKeys.me,
    queryFn: async () => {
      const res = await apiFetch<UserRead>("/api/v1/me");
      if (!res.data) {
        throw new Error("me_not_found");
      }
      return res.data;
    },
    enabled,
  });
}
