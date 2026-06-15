"use client";

import { useMemo, useState } from "react";

import { useDemoAnalysisTemplates } from "@/hooks/use-demo-analysis-templates";
import { useWc2022Matches } from "@/hooks/use-wc2022-matches";
import {
  formatMatchLabel,
  type WcMatchBrief,
} from "@/lib/worldcup-types";

type Wc2022MatchPickerProps = {
  disabled?: boolean;
  onRunDemoAnalysis?: (match: WcMatchBrief, templateId: string) => void;
};

export function Wc2022MatchPicker({
  disabled = false,
  onRunDemoAnalysis,
}: Wc2022MatchPickerProps) {
  const { data, isLoading, isError } = useWc2022Matches();
  const {
    data: templates = [],
    isLoading: templatesLoading,
    isError: templatesError,
  } = useDemoAnalysisTemplates();
  const stages = data?.stages ?? [];
  const [stageName, setStageName] = useState<string>("");
  const [selectedMatchId, setSelectedMatchId] = useState<string>("");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");

  const activeStageName = stageName || stages[0]?.stage_name || "";
  const matches = useMemo(() => {
    const stage = stages.find((item) => item.stage_name === activeStageName);
    return stage?.matches ?? [];
  }, [stages, activeStageName]);

  const activeMatch =
    matches.find((item) => item.id === selectedMatchId) ?? null;

  const canStart =
    Boolean(activeMatch) &&
    Boolean(selectedTemplateId) &&
    !disabled;

  const handleStart = () => {
    if (!activeMatch || !selectedTemplateId) {
      return;
    }
    onRunDemoAnalysis?.(activeMatch, selectedTemplateId);
  };

  if (isLoading || templatesLoading) {
    return (
      <p className="text-xs text-zinc-500">加载 2022 世界杯赛程与分析模板…</p>
    );
  }

  if (isError || templatesError) {
    return (
      <p className="text-xs text-red-600">赛程或分析模板加载失败</p>
    );
  }

  if (!stages.length) {
    return (
      <p className="text-xs text-zinc-500">
        暂无比赛数据（需运行 World Cup ETL）
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2 lg:flex-row lg:flex-wrap lg:items-end">
      <label className="flex flex-col gap-1 text-xs text-zinc-500">
        <span>2022 世界杯 · 阶段</span>
        <select
          value={activeStageName}
          disabled={disabled}
          onChange={(e) => {
            setStageName(e.target.value);
            setSelectedMatchId("");
            setSelectedTemplateId("");
          }}
          className="rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-800 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
        >
          {stages.map((stage) => (
            <option key={stage.stage_name} value={stage.stage_name}>
              {stage.stage_label}（{stage.matches.length} 场）
            </option>
          ))}
        </select>
      </label>
      <label className="flex min-w-0 flex-col gap-1 text-xs text-zinc-500 lg:max-w-md">
        <span>比赛（日期倒序）</span>
        <select
          value={selectedMatchId}
          disabled={disabled || matches.length === 0}
          onChange={(e) => {
            setSelectedMatchId(e.target.value);
            setSelectedTemplateId("");
          }}
          className="min-w-0 rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-800 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
        >
          <option value="">选择比赛…</option>
          {matches.map((match) => (
            <option key={match.id} value={match.id}>
              {match.match_date} · {formatMatchLabel(match)}
            </option>
          ))}
        </select>
      </label>
      <label className="flex min-w-0 flex-col gap-1 text-xs text-zinc-500 lg:max-w-xs">
        <span>分析维度（演示）</span>
        <select
          value={selectedTemplateId}
          disabled={disabled || !activeMatch}
          onChange={(e) => setSelectedTemplateId(e.target.value)}
          className="min-w-0 rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-800 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
        >
          <option value="">
            {activeMatch ? "选择分析维度…" : "请先选择比赛"}
          </option>
          {templates.map((template) => (
            <option key={template.id} value={template.id}>
              {template.label}
            </option>
          ))}
        </select>
      </label>
      <button
        type="button"
        disabled={!canStart}
        onClick={handleStart}
        className="rounded-lg bg-emerald-700 px-4 py-1.5 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50 dark:bg-emerald-600 dark:hover:bg-emerald-500"
      >
        开始分析
      </button>
    </div>
  );
}
