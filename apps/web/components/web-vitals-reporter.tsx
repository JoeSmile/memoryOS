"use client";

import { useReportWebVitals } from "next/web-vitals";
import { useCallback, useState } from "react";

import { DevVitalsIndicator } from "@/components/dev-vitals-indicator";
import {
  isWebVitalsAlert,
  reportWebVitalInDev,
  toWebVitalsAlert,
  type WebVitalsAlert,
} from "@/lib/web-vitals-dev";

const isDev = process.env.NODE_ENV === "development";

export function WebVitalsReporter() {
  const [alert, setAlert] = useState<WebVitalsAlert | null>(null);
  const dismissAlert = useCallback(() => setAlert(null), []);

  useReportWebVitals((metric) => {
    if (!isDev) {
      return;
    }

    const snapshot = {
      id: metric.id,
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
    };

    reportWebVitalInDev(snapshot);

    if (isWebVitalsAlert(snapshot.rating)) {
      setAlert(toWebVitalsAlert(snapshot));
    }
  });

  return <DevVitalsIndicator alert={alert} onDismiss={dismissAlert} />;
}
