"use client";

import type { UIMessage } from "ai";
import { useState } from "react";

import {
  TOOL_CALL_DATA_PART_TYPE,
  TOOL_RESULT_DATA_PART_TYPE,
  type ToolCallDataPart,
  type ToolResultDataPart,
  type ToolStepItem,
} from "@/lib/chat-types";

export type ToolTimelineEntryStatus = "pending" | "success" | "failure";

export type ToolTimelineEntry = {
  id: string;
  name: string;
  status: ToolTimelineEntryStatus;
  summary?: string;
  duration_ms?: number;
  arguments?: Record<string, unknown>;
};

const isDev = process.env.NODE_ENV === "development";

function entryFromStep(step: ToolStepItem): ToolTimelineEntry {
  return {
    id: step.id,
    name: step.name,
    status: step.success ? "success" : "failure",
    summary: step.summary,
    duration_ms: step.duration_ms,
    arguments: step.arguments,
  };
}

export function collectToolTimelineEntries(
  message: UIMessage,
  fallbackSteps: ToolStepItem[] | null,
): ToolTimelineEntry[] {
  const ordered: ToolTimelineEntry[] = [];

  for (const part of message.parts) {
    if (part.type === TOOL_CALL_DATA_PART_TYPE) {
      const data = (part as ToolCallDataPart).data;
      if (typeof data.id !== "string" || data.id.length === 0) {
        continue;
      }
      ordered.push({
        id: data.id,
        name: data.name,
        status: "pending",
        arguments: data.arguments,
      });
      continue;
    }
    if (part.type !== TOOL_RESULT_DATA_PART_TYPE) {
      continue;
    }
    const data = (part as ToolResultDataPart).data;
    if (typeof data.id !== "string" || data.id.length === 0) {
      continue;
    }
    const idx = ordered.findIndex((entry) => entry.id === data.id);
    const updated: ToolTimelineEntry = {
      id: data.id,
      name: data.name,
      status: data.success ? "success" : "failure",
      summary: data.summary,
      ...(data.duration_ms != null ? { duration_ms: data.duration_ms } : {}),
      arguments: idx >= 0 ? ordered[idx]?.arguments : undefined,
    };
    if (idx >= 0) {
      ordered[idx] = updated;
    } else {
      ordered.push(updated);
    }
  }

  if (ordered.length > 0) {
    return ordered;
  }

  if (fallbackSteps?.length) {
    return fallbackSteps.map(entryFromStep);
  }

  return [];
}

function statusLabel(status: ToolTimelineEntryStatus): string {
  if (status === "pending") {
    return "执行中";
  }
  if (status === "success") {
    return "成功";
  }
  return "失败";
}

function statusTone(status: ToolTimelineEntryStatus): string {
  if (status === "pending") {
    return "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-900 dark:bg-sky-950/50 dark:text-sky-200";
  }
  if (status === "success") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200";
  }
  return "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-200";
}

type ToolTimelineRowProps = {
  entry: ToolTimelineEntry;
};

function ToolTimelineRow({ entry }: ToolTimelineRowProps) {
  const [expanded, setExpanded] = useState(isDev);
  const hasSummary = Boolean(entry.summary?.trim());
  const showSummary = hasSummary && (isDev || expanded);

  return (
    <li className="relative pl-5">
      <span
        className={`absolute left-0 top-1.5 h-2 w-2 rounded-full border ${
          entry.status === "pending"
            ? "animate-pulse border-sky-400 bg-sky-300 dark:border-sky-600 dark:bg-sky-700"
            : entry.status === "success"
              ? "border-emerald-500 bg-emerald-400 dark:border-emerald-600 dark:bg-emerald-500"
              : "border-rose-500 bg-rose-400 dark:border-rose-600 dark:bg-rose-500"
        }`}
        aria-hidden
      />
      <div
        className={`rounded-lg border px-2.5 py-1.5 text-xs ${statusTone(entry.status)}`}
      >
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span className="font-medium">{entry.name}</span>
          <span className="opacity-75">· {statusLabel(entry.status)}</span>
          {entry.duration_ms != null ? (
            <span className="opacity-75">· {entry.duration_ms}ms</span>
          ) : null}
          {!isDev && hasSummary ? (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="ml-auto text-[11px] underline opacity-80 hover:opacity-100"
            >
              {expanded ? "收起" : "详情"}
            </button>
          ) : null}
        </div>
        {showSummary ? (
          <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed opacity-90">
            {entry.summary}
          </p>
        ) : null}
      </div>
    </li>
  );
}

type ToolTimelineProps = {
  message: UIMessage;
  steps: ToolStepItem[] | null;
  isStreaming?: boolean;
};

export function ToolTimeline({
  message,
  steps,
  isStreaming = false,
}: ToolTimelineProps) {
  const entries = collectToolTimelineEntries(message, steps);
  if (entries.length === 0) {
    return null;
  }

  return (
    <div
      className="mb-2"
      aria-label="工具调用"
      data-testid="tool-timeline"
      data-streaming={isStreaming ? "true" : undefined}
    >
      <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        工具调用
      </p>
      <ol className="space-y-2 border-l border-zinc-200 pl-0 dark:border-zinc-800">
        {entries.map((entry) => (
          <ToolTimelineRow key={entry.id} entry={entry} />
        ))}
      </ol>
    </div>
  );
}
