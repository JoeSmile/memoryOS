import { describe, expect, it } from "vitest";

import { shouldShowListThinking } from "@/lib/chat-thinking-state";

describe("shouldShowListThinking", () => {
  it("is hidden when idle", () => {
    expect(shouldShowListThinking(false, false, "user")).toBe(false);
    expect(shouldShowListThinking(false, false, "assistant")).toBe(false);
    expect(shouldShowListThinking(false, false, undefined)).toBe(false);
  });

  it("shows during demo-turn wait (isSending, not streaming)", () => {
    expect(shouldShowListThinking(true, false, "user")).toBe(true);
    expect(shouldShowListThinking(true, false, "assistant")).toBe(true);
    expect(shouldShowListThinking(true, false, undefined)).toBe(true);
  });

  it("shows while streaming before assistant row exists", () => {
    expect(shouldShowListThinking(false, true, "user")).toBe(true);
    expect(shouldShowListThinking(false, true, undefined)).toBe(true);
  });

  it("hides footer indicator when streaming assistant row exists (in-bubble placeholder)", () => {
    expect(shouldShowListThinking(false, true, "assistant")).toBe(false);
  });

  it("prefers in-bubble placeholder when both sending and streaming with assistant last", () => {
    expect(shouldShowListThinking(true, true, "assistant")).toBe(false);
  });

  it("shows footer when streaming with user last even if isSending still true", () => {
    expect(shouldShowListThinking(true, true, "user")).toBe(true);
  });
});
