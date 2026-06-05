"use client";

import { useEffect } from "react";

import {
  formatWebVitalValue,
  type WebVitalsAlert,
} from "@/lib/web-vitals-dev";

const ALERT_TTL_MS = 12_000;

type DevVitalsIndicatorProps = {
  alert: WebVitalsAlert | null;
  onDismiss: () => void;
};

export function DevVitalsIndicator({ alert, onDismiss }: DevVitalsIndicatorProps) {
  useEffect(() => {
    if (!alert) {
      return;
    }

    const timer = window.setTimeout(onDismiss, ALERT_TTL_MS);
    return () => window.clearTimeout(timer);
  }, [alert, onDismiss]);

  if (!alert) {
    return null;
  }

  const isPoor = alert.rating === "poor";
  const value = formatWebVitalValue(alert.name, alert.value);

  return (
    <div
      role="status"
      aria-live="polite"
      className={`pointer-events-auto fixed bottom-4 right-4 z-50 max-w-xs rounded-lg border px-3 py-2 text-xs shadow-md backdrop-blur-sm ${
        isPoor
          ? "border-amber-500/60 bg-amber-950/90 text-amber-100"
          : "border-yellow-500/50 bg-yellow-950/85 text-yellow-100"
      }`}
    >
      <div className="flex items-start gap-2">
        <span aria-hidden className="mt-0.5 shrink-0">
          {isPoor ? "⚠" : "◦"}
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-medium">
            {alert.name} {value} · {alert.rating}
          </p>
          <p className="mt-0.5 truncate opacity-80">{alert.path}</p>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded px-1 opacity-70 hover:opacity-100"
          aria-label="关闭性能提示"
        >
          ×
        </button>
      </div>
    </div>
  );
}
