import { describe, expect, it } from "vitest";

import { formatTokenCount } from "@/lib/format-token-count";

describe("formatTokenCount", () => {
  it("formats sub-thousand values as integers", () => {
    expect(formatTokenCount(0)).toBe("0");
    expect(formatTokenCount(999)).toBe("999");
  });

  it("formats thousands with K suffix", () => {
    expect(formatTokenCount(1_500)).toBe("1.5K");
    expect(formatTokenCount(200_000)).toBe("200K");
  });

  it("formats millions with M suffix", () => {
    expect(formatTokenCount(200_100_000)).toBe("200.1M");
    expect(formatTokenCount(1_000_000)).toBe("1M");
  });
});
