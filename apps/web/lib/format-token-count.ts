function trimOneDecimal(value: number): string {
  const text = value.toFixed(1);
  return text.endsWith(".0") ? text.slice(0, -2) : text;
}

/** Human-readable token counts: 999 → "999", 200_000 → "200K", 200_100_000 → "200.1M". */
export function formatTokenCount(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return "0";
  }
  if (value < 1_000) {
    return String(Math.round(value));
  }
  if (value < 1_000_000) {
    const scaled = value / 1_000;
    return scaled >= 100
      ? `${Math.round(scaled)}K`
      : `${trimOneDecimal(scaled)}K`;
  }
  const scaled = value / 1_000_000;
  const roundedTenth = Math.round(scaled * 10) / 10;
  if (Number.isInteger(roundedTenth)) {
    return `${Math.round(roundedTenth)}M`;
  }
  return `${trimOneDecimal(roundedTenth)}M`;
}
