export type WebVitalsMetricName =
  | "CLS"
  | "FCP"
  | "FID"
  | "INP"
  | "LCP"
  | "TTFB";

export type WebVitalsRating = "good" | "needs-improvement" | "poor";

export type WebVitalsMetric = {
  id: string;
  name: WebVitalsMetricName;
  value: number;
  rating?: WebVitalsRating;
};

export type WebVitalsAlert = {
  id: string;
  name: WebVitalsMetricName;
  value: number;
  rating: WebVitalsRating;
  path: string;
};

const isDev = process.env.NODE_ENV === "development";
const verbose = process.env.NEXT_PUBLIC_WEB_VITALS_VERBOSE === "1";
const STORAGE_PREFIX = "memoryos:wv:";

/** 内存兜底：sessionStorage 不可用时 */
const memoryAlertedKeys = new Set<string>();

export function isWebVitalsAlert(rating: WebVitalsRating | undefined): boolean {
  if (rating === "poor") {
    return true;
  }
  if (verbose && rating === "needs-improvement") {
    return true;
  }
  return false;
}

function storageKey(path: string, name: WebVitalsMetricName): string {
  return `${STORAGE_PREFIX}${path}:${name}`;
}

export function shouldEmitWebVitalsAlert(
  path: string,
  name: WebVitalsMetricName,
): boolean {
  const key = storageKey(path, name);

  try {
    if (sessionStorage.getItem(key)) {
      return false;
    }
    sessionStorage.setItem(key, "1");
    return true;
  } catch {
    if (memoryAlertedKeys.has(key)) {
      return false;
    }
    memoryAlertedKeys.add(key);
    return true;
  }
}

export function formatWebVitalValue(name: WebVitalsMetricName, value: number): string {
  if (name === "CLS") {
    return value.toFixed(4);
  }
  if (name === "TTFB" || name === "FCP" || name === "LCP" || name === "INP") {
    return `${Math.round(value)}ms`;
  }
  return String(Math.round(value));
}

export function formatWebVitalLine(
  metric: Pick<WebVitalsMetric, "name" | "value" | "rating">,
): string {
  const rating = metric.rating ?? "-";
  return `${metric.name}=${formatWebVitalValue(metric.name, metric.value)} (${rating})`;
}

/** @returns whether a throttled alert was emitted */
export function reportWebVitalInDev(metric: WebVitalsMetric): boolean {
  if (!isDev || !isWebVitalsAlert(metric.rating)) {
    if (isDev && verbose) {
      console.info(
        `[WebVitals] ${formatWebVitalLine(metric)} id=${metric.id}`,
      );
    }
    return false;
  }

  const path =
    typeof window !== "undefined" ? window.location.pathname : "/";
  if (!shouldEmitWebVitalsAlert(path, metric.name)) {
    return false;
  }

  console.warn(`[WebVitals ⚠] ${path} ${formatWebVitalLine(metric)}`);
  return true;
}

export function toWebVitalsAlert(metric: WebVitalsMetric): WebVitalsAlert {
  return {
    id: metric.id,
    name: metric.name,
    value: metric.value,
    rating: metric.rating ?? "poor",
    path: window.location.pathname,
  };
}
