"use client";

import { useEffect, useId, useRef, useState } from "react";

import type { RagSourceItem } from "@/lib/chat-types";

type RagSourceChipProps = {
  item: RagSourceItem;
};

function chipTooltip(item: RagSourceItem): string {
  const preview = item.content_preview.slice(0, 60);
  const suffix = item.content_preview.length > 60 ? "…" : "";
  return `${item.external_id} · ${preview}${suffix}`;
}

function formatScore(score: number): string {
  return score.toFixed(2);
}

export function RagSourceChip({ item }: RagSourceChipProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) {
      return;
    }
    function onPointerDown(event: MouseEvent) {
      if (rootRef.current?.contains(event.target as Node)) {
        return;
      }
      setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        title={chipTooltip(item)}
        aria-expanded={open}
        aria-controls={panelId}
        aria-haspopup="dialog"
        onClick={() => setOpen((value) => !value)}
        className="max-w-[12rem] truncate rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 hover:bg-emerald-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/60 dark:border-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200 dark:hover:bg-emerald-900/60"
      >
        {item.external_id}
      </button>
      {open ? (
        <div
          id={panelId}
          role="dialog"
          aria-label={`来源 ${item.external_id}`}
          className="absolute bottom-full left-0 z-20 mb-1.5 w-72 rounded-lg border border-zinc-200 bg-white p-3 text-left shadow-lg dark:border-zinc-700 dark:bg-zinc-900"
        >
          <p className="text-xs leading-relaxed whitespace-pre-wrap text-zinc-700 dark:text-zinc-200">
            {item.content_preview}
          </p>
          <dl className="mt-2 space-y-1 border-t border-zinc-100 pt-2 text-[11px] text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
            <div className="flex gap-2">
              <dt className="shrink-0">ID</dt>
              <dd className="min-w-0 break-all">{item.external_id}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="shrink-0">集合</dt>
              <dd className="min-w-0 break-all">{item.collection}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="shrink-0">相关度</dt>
              <dd>{formatScore(item.score)}</dd>
            </div>
            {item.entity_type ? (
              <div className="flex gap-2">
                <dt className="shrink-0">类型</dt>
                <dd>{item.entity_type}</dd>
              </div>
            ) : null}
          </dl>
        </div>
      ) : null}
    </div>
  );
}

type RagSourceChipListProps = {
  items: RagSourceItem[];
};

export function RagSourceChipList({ items }: RagSourceChipListProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div
      className="mb-2 flex flex-wrap gap-1.5"
      aria-label="参考来源"
      data-testid="rag-source-chips"
    >
      {items.map((item, index) => (
        <RagSourceChip
          key={`${item.external_id}-${item.collection}-${index}`}
          item={item}
        />
      ))}
    </div>
  );
}
