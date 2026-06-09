import { describe, expect, it } from "vitest";

import { collectToolTimelineEntries } from "@/components/chat/tool-timeline";
import {
  TOOL_CALL_DATA_PART_TYPE,
  TOOL_RESULT_DATA_PART_TYPE,
  getToolStepsFromMessageRead,
  getToolStepsFromUIMessage,
  parseToolStepsFromMetadata,
  toUIMessages,
  type MessageRead,
} from "@/lib/chat-types";

const SAMPLE_STEP = {
  id: "call_abc",
  name: "tavily_search",
  arguments: { query: "2026 world cup" },
  success: true,
  summary: "Found 3 results about hosts.",
  duration_ms: 840,
};

describe("parseToolStepsFromMetadata", () => {
  it("returns null for missing or invalid metadata", () => {
    expect(parseToolStepsFromMetadata(null)).toBeNull();
    expect(parseToolStepsFromMetadata({})).toBeNull();
    expect(
      parseToolStepsFromMetadata({ tool_steps: [{ id: "", name: "x" }] }),
    ).toBeNull();
  });

  it("parses valid tool_steps array", () => {
    const steps = parseToolStepsFromMetadata({ tool_steps: [SAMPLE_STEP] });
    expect(steps).toEqual([SAMPLE_STEP]);
  });
});

describe("getToolStepsFromUIMessage", () => {
  it("merges tool call and result data parts in order", () => {
    const message = {
      id: "m1",
      role: "assistant" as const,
      parts: [
        {
          type: TOOL_CALL_DATA_PART_TYPE,
          data: {
            id: "call_abc",
            name: "tavily_search",
            arguments: { query: "x" },
          },
        },
        {
          type: TOOL_RESULT_DATA_PART_TYPE,
          data: {
            id: "call_abc",
            name: "tavily_search",
            success: false,
            summary: "timeout",
          },
        },
      ],
    };

    expect(getToolStepsFromUIMessage(message)).toEqual([
      {
        id: "call_abc",
        name: "tavily_search",
        arguments: { query: "x" },
        success: false,
        summary: "timeout",
      },
    ]);
  });

  it("falls back to metadata.toolSteps when parts have no tool data", () => {
    const message = {
      id: "m2",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: "answer" }],
      metadata: { toolSteps: [SAMPLE_STEP] },
    };

    expect(getToolStepsFromUIMessage(message)).toEqual([SAMPLE_STEP]);
  });
});

describe("toUIMessages tool_steps hydrate", () => {
  it("round-trips metadata.tool_steps into data parts and metadata", () => {
    const row: MessageRead = {
      id: "msg-1",
      role: "assistant",
      content: "Based on search…",
      created_at: "2026-06-08T00:00:00Z",
      metadata: { tool_steps: [SAMPLE_STEP] },
    };

    const [ui] = toUIMessages([row]);
    expect(ui.parts[0]).toMatchObject({
      type: TOOL_CALL_DATA_PART_TYPE,
      data: {
        id: SAMPLE_STEP.id,
        name: SAMPLE_STEP.name,
        arguments: SAMPLE_STEP.arguments,
      },
    });
    expect(ui.parts[1]).toMatchObject({
      type: TOOL_RESULT_DATA_PART_TYPE,
      data: {
        id: SAMPLE_STEP.id,
        success: true,
        summary: SAMPLE_STEP.summary,
        duration_ms: SAMPLE_STEP.duration_ms,
      },
    });
    expect(getToolStepsFromUIMessage(ui)).toEqual([SAMPLE_STEP]);
    expect(getToolStepsFromMessageRead(row)).toEqual([SAMPLE_STEP]);
  });
});

describe("collectToolTimelineEntries", () => {
  it("shows pending status for call without result during streaming", () => {
    const message = {
      id: "m3",
      role: "assistant" as const,
      parts: [
        {
          type: TOOL_CALL_DATA_PART_TYPE,
          data: {
            id: "call_pending",
            name: "tavily_search",
            arguments: { query: "q" },
          },
        },
      ],
    };

    expect(collectToolTimelineEntries(message, null)).toEqual([
      {
        id: "call_pending",
        name: "tavily_search",
        status: "pending",
        arguments: { query: "q" },
      },
    ]);
  });
});
