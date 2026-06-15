"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { WcTournamentMatchesRead } from "@/lib/worldcup-types";

export const WC_2022_TOURNAMENT_ID = "WC-2022";

export async function fetchWc2022Matches(): Promise<WcTournamentMatchesRead> {
  const res = await apiFetch<WcTournamentMatchesRead>(
    `/api/v1/worldcup/matches?tournament_id=${WC_2022_TOURNAMENT_ID}`,
  );
  return res.data ?? {
    tournament_id: WC_2022_TOURNAMENT_ID,
    tournament_name: "",
    stages: [],
  };
}

export function useWc2022Matches(enabled = true) {
  return useQuery({
    queryKey: ["worldcup", "matches", WC_2022_TOURNAMENT_ID],
    queryFn: fetchWc2022Matches,
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}
