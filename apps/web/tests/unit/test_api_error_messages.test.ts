import { describe, expect, it } from "vitest";

import { resolveApiErrorMessage } from "@/lib/api-error-messages";

describe("resolveApiErrorMessage", () => {
  it("maps token_quota_exceeded to Chinese detail from data", () => {
    expect(
      resolveApiErrorMessage(42902, "token_quota_exceeded", {
        detail: "配额已用尽",
      }),
    ).toBe("配额已用尽");
  });

  it("falls back to default Chinese when detail missing", () => {
    expect(
      resolveApiErrorMessage(42902, "token_quota_exceeded", null),
    ).toContain("今日");
  });
});
