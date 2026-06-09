import { describe, expect, it } from "vitest";

import {
  extractToolCallPayload,
  extractToolResultPayload,
  parseSseDataLine,
} from "@/lib/sse-frames";

function frame(event: string, data: Record<string, unknown>) {
  return { event, data };
}

describe("extractToolCallPayload", () => {
  it("parses valid tool_call frames", () => {
    const parsed = extractToolCallPayload(
      frame("tool_call", {
        id: "call_1",
        name: "tavily_search",
        arguments: { query: "world cup" },
      }),
    );
    expect(parsed).toEqual({
      id: "call_1",
      name: "tavily_search",
      arguments: { query: "world cup" },
    });
  });

  it("defaults missing arguments to an empty object", () => {
    const parsed = extractToolCallPayload(
      frame("tool_call", { id: "call_1", name: "tavily_search" }),
    );
    expect(parsed?.arguments).toEqual({});
  });

  it("returns null for wrong event or invalid payload", () => {
    expect(extractToolCallPayload(frame("token", { content: "x" }))).toBeNull();
    expect(
      extractToolCallPayload(frame("tool_call", { id: "", name: "x" })),
    ).toBeNull();
    expect(
      extractToolCallPayload(
        frame("tool_call", { id: "c1", name: "x", arguments: [] }),
      ),
    ).toBeNull();
  });
});

describe("extractToolResultPayload", () => {
  it("parses valid tool_result frames", () => {
    const parsed = extractToolResultPayload(
      frame("tool_result", {
        id: "call_1",
        name: "tavily_search",
        success: true,
        summary: "mock summary",
        duration_ms: 42,
      }),
    );
    expect(parsed).toEqual({
      id: "call_1",
      name: "tavily_search",
      success: true,
      summary: "mock summary",
      duration_ms: 42,
    });
  });

  it("includes error when present", () => {
    const parsed = extractToolResultPayload(
      frame("tool_result", {
        id: "call_1",
        name: "tavily_search",
        success: false,
        summary: "tool_error: timeout",
        error: "tool_error: timeout",
      }),
    );
    expect(parsed?.success).toBe(false);
    expect(parsed?.error).toBe("tool_error: timeout");
  });

  it("returns null for wrong event or invalid payload", () => {
    expect(extractToolResultPayload(frame("tool_call", {}))).toBeNull();
    expect(
      extractToolResultPayload(
        frame("tool_result", {
          id: "c1",
          name: "x",
          success: "yes",
          summary: "s",
        }),
      ),
    ).toBeNull();
  });
});

describe("parseSseDataLine tool events", () => {
  it("round-trips tool frames from SSE lines", () => {
    const line =
      'data: {"event":"tool_call","data":{"id":"c1","name":"tavily_search","arguments":{"query":"q"}}}';
    const frame_ = parseSseDataLine(line);
    expect(frame_).not.toBeNull();
    expect(extractToolCallPayload(frame_!)).toEqual({
      id: "c1",
      name: "tavily_search",
      arguments: { query: "q" },
    });
  });
});
