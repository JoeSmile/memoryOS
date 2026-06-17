"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchMyUsage } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";
import { chatQueryKeys } from "@/lib/chat-query-keys";

export function useMyUsage(enabled = true) {
  const hasToken = Boolean(getAccessToken());

  return useQuery({
    queryKey: chatQueryKeys.myUsage,
    queryFn: fetchMyUsage,
    enabled: enabled && hasToken,
    staleTime: 30_000,
  });
}
