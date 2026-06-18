import { describe, expect, it } from "vitest";

import {
  memoryosSseResponseToDataStream,
  RAG_SOURCES_UI_DATA_TYPE,
  TOOL_CALL_UI_DATA_TYPE,
  TOOL_RESULT_UI_DATA_TYPE,
} from "@/lib/memoryos-upstream";
import { extractDonePayload, parseSseDataLine } from "@/lib/sse-frames";
import type { RagSourceItem } from "@/lib/sse-frames";

const SAMPLE_SOURCES: RagSourceItem[] = [
  {
    external_id: "match:M-2022-64",
    collection: "worldcup-samples",
    score: 0.88,
    content_preview: "Argentina vs France final",
  },
];

const MESSAGE_ID = "11111111-1111-4111-8111-111111111111";

function sseFrame(event: string, data: Record<string, unknown>): string {
  return `data: ${JSON.stringify({ event, data })}\n\n`;
}

function mockSseResponse(body: string): Response {
  return new Response(
    new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(body));
        controller.close();
      },
    }),
    {
      headers: { "Content-Type": "text/event-stream" },
    },
  );
}

type UiStreamPart = Record<string, unknown>;

async function readUiStreamParts(
  stream: ReadableStream<Uint8Array>,
): Promise<UiStreamPart[]> {
  const decoder = new TextDecoder();
  let buffer = "";

  for await (const chunk of stream as AsyncIterable<Uint8Array>) {
    buffer += decoder.decode(chunk, { stream: true });
  }
  buffer += decoder.decode();

  const parts: UiStreamPart[] = [];
  for (const block of buffer.split("\n\n")) {
    const trimmed = block.trim();
    if (!trimmed.startsWith("data:")) {
      continue;
    }
    const payload = trimmed.slice(5).trim();
    if (payload === "[DONE]") {
      continue;
    }
    parts.push(JSON.parse(payload) as UiStreamPart);
  }
  return parts;
}

function partTypes(parts: UiStreamPart[]): string[] {
  return parts.map((part) => String(part.type));
}

describe("memoryosSseResponseToDataStream", () => {
  it("parses done SSE lines for harness fixtures", () => {
    const line = sseFrame("done", {
      message_id: MESSAGE_ID,
      sources: SAMPLE_SOURCES,
    }).trim();
    const frame = parseSseDataLine(line);
    expect(frame).not.toBeNull();
    expect(extractDonePayload(frame!)).toEqual({
      message_id: MESSAGE_ID,
      sources: SAMPLE_SOURCES,
    });
  });

  it("maps sources before text and emits message-metadata on done", async () => {
    const upstream = mockSseResponse(
      [
        sseFrame("start", { stream_id: "stream-abc" }),
        sseFrame("sources", { items: SAMPLE_SOURCES }),
        sseFrame("token", { content: "你" }),
        sseFrame("token", { content: "好" }),
        sseFrame("done", {
          message_id: MESSAGE_ID,
          sources: SAMPLE_SOURCES,
        }),
      ].join(""),
    );

    const parts = await readUiStreamParts(
      memoryosSseResponseToDataStream(upstream),
    );
    const types = partTypes(parts);

    expect(types).toContain("start");
    expect(types).toContain("start-step");
    expect(types.indexOf(RAG_SOURCES_UI_DATA_TYPE)).toBeLessThan(
      types.indexOf("text-start"),
    );

    const ragPart = parts.find(
      (part) => part.type === RAG_SOURCES_UI_DATA_TYPE,
    );
    expect(ragPart?.data).toEqual({ items: SAMPLE_SOURCES });

    const textDeltas = parts.filter((part) => part.type === "text-delta");
    expect(textDeltas.map((part) => part.delta).join("")).toEqual("你好");

    const metadataPart = parts.find((part) => part.type === "message-metadata");
    expect(metadataPart?.messageMetadata).toEqual({
      messageId: MESSAGE_ID,
      ragSources: SAMPLE_SOURCES,
    });

    expect(types.at(-2)).toBe("finish-step");
    expect(types.at(-1)).toBe("finish");
  });

  it("emits text-only stream when upstream has no sources", async () => {
    const plainMessageId = "22222222-2222-4222-8222-222222222222";
    const upstream = mockSseResponse(
      [
        sseFrame("start", { stream_id: "stream-plain" }),
        sseFrame("token", { content: "hello" }),
        sseFrame("done", { message_id: plainMessageId }),
      ].join(""),
    );

    const parts = await readUiStreamParts(
      memoryosSseResponseToDataStream(upstream),
    );
    const types = partTypes(parts);

    expect(types).not.toContain(RAG_SOURCES_UI_DATA_TYPE);
    expect(types).toContain("text-start");
    expect(types).toContain("text-delta");
    expect(types).toContain("text-end");

    const metadataPart = parts.find((part) => part.type === "message-metadata");
    expect(metadataPart?.messageMetadata).toEqual({
      messageId: plainMessageId,
    });
  });

  it("maps tool_call and tool_result before text in ReAct order", async () => {
    const upstream = mockSseResponse(
      [
        sseFrame("start", { stream_id: "stream-react" }),
        sseFrame("tool_call", {
          id: "mock_call_tavily",
          name: "tavily_search",
          arguments: { query: "mock web search" },
        }),
        sseFrame("tool_result", {
          id: "mock_call_tavily",
          name: "tavily_search",
          success: true,
          summary: "mock summary",
          duration_ms: 12,
        }),
        sseFrame("token", { content: "联" }),
        sseFrame("token", { content: "网" }),
        sseFrame("done", { message_id: MESSAGE_ID }),
      ].join(""),
    );

    const parts = await readUiStreamParts(
      memoryosSseResponseToDataStream(upstream),
    );
    const types = partTypes(parts);

    const toolCallIndex = types.indexOf(TOOL_CALL_UI_DATA_TYPE);
    const toolResultIndex = types.indexOf(TOOL_RESULT_UI_DATA_TYPE);
    const textStartIndex = types.indexOf("text-start");

    expect(toolCallIndex).toBeGreaterThanOrEqual(0);
    expect(toolResultIndex).toBeGreaterThan(toolCallIndex);
    expect(textStartIndex).toBeGreaterThan(toolResultIndex);

    const toolCallPart = parts.find(
      (part) => part.type === TOOL_CALL_UI_DATA_TYPE,
    );
    expect(toolCallPart?.data).toEqual({
      id: "mock_call_tavily",
      name: "tavily_search",
      arguments: { query: "mock web search" },
    });

    const toolResultPart = parts.find(
      (part) => part.type === TOOL_RESULT_UI_DATA_TYPE,
    );
    expect(toolResultPart?.data).toEqual({
      id: "mock_call_tavily",
      name: "tavily_search",
      success: true,
      summary: "mock summary",
      duration_ms: 12,
    });

    const textDeltas = parts.filter((part) => part.type === "text-delta");
    expect(textDeltas.map((part) => part.delta).join("")).toEqual("联网");
  });

  it("closes text before tool round then resumes text after tool_result", async () => {
    const upstream = mockSseResponse(
      [
        sseFrame("start", { stream_id: "stream-react-mid" }),
        sseFrame("sources", { items: SAMPLE_SOURCES }),
        sseFrame("token", { content: "根" }),
        sseFrame("token", { content: "据" }),
        sseFrame("tool_call", {
          id: "call_1",
          name: "tavily_search",
          arguments: { query: "2022 top scorers" },
        }),
        sseFrame("tool_result", {
          id: "call_1",
          name: "tavily_search",
          success: true,
          summary: "mock summary",
        }),
        sseFrame("token", { content: "1" }),
        sseFrame("token", { content: "." }),
        sseFrame("done", { message_id: MESSAGE_ID }),
      ].join(""),
    );

    const parts = await readUiStreamParts(
      memoryosSseResponseToDataStream(upstream),
    );
    const types = partTypes(parts);

    const firstTextEnd = types.indexOf("text-end");
    const toolCallIndex = types.indexOf(TOOL_CALL_UI_DATA_TYPE);
    const secondTextStart = types.indexOf("text-start", firstTextEnd + 1);

    expect(firstTextEnd).toBeGreaterThan(types.indexOf("text-delta"));
    expect(toolCallIndex).toBeGreaterThan(firstTextEnd);
    expect(secondTextStart).toBeGreaterThan(toolCallIndex);

    const textDeltas = parts.filter((part) => part.type === "text-delta");
    expect(textDeltas.map((part) => part.delta).join("")).toEqual("根据1.");
  });
});
