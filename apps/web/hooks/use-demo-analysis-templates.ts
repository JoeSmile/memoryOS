"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";

export type DemoAnalysisTemplate = {
  id: string;
  label: string;
  description: string;
};

export async function fetchDemoAnalysisTemplates(): Promise<DemoAnalysisTemplate[]> {
  const res = await apiFetch<DemoAnalysisTemplate[]>(
    "/api/v1/worldcup/demo-templates",
  );
  return res.data ?? [];
}

export function useDemoAnalysisTemplates(enabled = true) {
  return useQuery({
    queryKey: ["worldcup", "demo-templates"],
    queryFn: fetchDemoAnalysisTemplates,
    enabled,
    staleTime: 10 * 60 * 1000,
  });
}
