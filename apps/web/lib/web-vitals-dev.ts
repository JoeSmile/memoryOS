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

export function isWebVitalsAlert(rating: WebVitalsRating | undefined): boolean {
  return rating === "needs-improvement" || rating === "poor";
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

export function reportWebVitalInDev(metric: WebVitalsMetric): void {
  if (!isDev) {
    return;
  }

  const line = formatWebVitalLine(metric);

  if (isWebVitalsAlert(metric.rating)) {
    console.warn(`[WebVitals ⚠] ${line}`);
    void postDevVitalsBeacon(metric);
    return;
  }

  if (verbose) {
    console.info(`[WebVitals] ${line} id=${metric.id}`);
  }
}

async function postDevVitalsBeacon(metric: WebVitalsMetric): Promise<void> {
  try {
    await fetch("/api/dev/vitals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: metric.name,
        value: metric.value,
        rating: metric.rating,
        path: window.location.pathname,
      }),
      keepalive: true,
    });
  } catch {
    // Dev-only helper; ignore network errors during HMR or offline.
  }
}

export function toWebVitalsAlert(metric: WebVitalsMetric): WebVitalsAlert {
  return {
    id: metric.id,
    name: metric.name,
    value: metric.value,
    rating: metric.rating ?? "needs-improvement",
    path: window.location.pathname,
  };
}
