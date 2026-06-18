import {
  extractDonePayload,
  extractSourcesItems,
  extractStartStreamId,
  extractTokenContent,
  extractToolCallPayload,
  extractToolResultPayload,
  parseSseDataLine,
  type MemoryosDonePayload,
  type MemoryosSseFrame,
  type RagSourceItem,
  type ToolCallPayload,
  type ToolResultPayload,
} from "@/lib/sse-frames";

/** Server-side FastAPI base (BFF). Prefer API_UPSTREAM_URL in Docker; browser uses NEXT_PUBLIC_API_URL. */
const API_BASE =
  process.env.API_UPSTREAM_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

/** Short assistant snapshots may inline full text; longer stops send length only. */
export const CANCEL_VISIBLE_CONTENT_INLINE_MAX = 256;

/** AI SDK UI message stream custom data part for RAG sources. */
export const RAG_SOURCES_UI_DATA_TYPE = "data-rag-sources" as const;

/** AI SDK UI message stream custom data parts for Unified ReAct tool rounds. */
export const TOOL_CALL_UI_DATA_TYPE = "data-tool-call" as const;
export const TOOL_RESULT_UI_DATA_TYPE = "data-tool-result" as const;

const UI_MESSAGE_TEXT_PART_ID = "text-1";
const UI_MESSAGE_STREAM_DONE = "data: [DONE]\n\n";

/** Batch upstream char tokens before emitting UI text-delta frames (fewer React updates). */
const TOKEN_COALESCE_MIN_CHARS = 16;

export type UpstreamChatParams = {
  conversationId: string;
  content: string;
  authorization: string | null;
  signal?: AbortSignal;
  clientMessageId?: string | null;
  regenerate?: boolean;
};

export type UpstreamCancelParams = {
  streamId: string;
  authorization: string | null;
  visibleContent?: string | null;
  visibleLength?: number | null;
};

export type CancelVisiblePayload = {
  visible_length?: number;
  visible_content?: string;
};

export type SseStreamOptions = {
  onStreamId?: (streamId: string) => void;
  /** Called once with drain+abort; wire to req.signal so Stop keeps upstream open until drained. */
  onClientAbort?: (drain: () => Promise<void>) => void;
  abortUpstream?: () => void;
};

/** @deprecated Use {@link SseStreamOptions}. */
export type SseTextStreamOptions = SseStreamOptions;

export type MemoryosUiDataStreamPart = Record<string, unknown>;

/** Build cancel body fields from local assistant text (Unicode code points). */
export function buildCancelVisiblePayload(
  visibleContent: string,
): CancelVisiblePayload {
  const visibleLength = [...visibleContent].length;
  if (visibleLength === 0) {
    return {};
  }
  return {
    visible_length: visibleLength,
    visible_content:
      visibleLength <= CANCEL_VISIBLE_CONTENT_INLINE_MAX
        ? visibleContent
        : undefined,
  };
}

function encodeUiMessageStreamPart(part: MemoryosUiDataStreamPart): Uint8Array {
  return new TextEncoder().encode(`data: ${JSON.stringify(part)}\n\n`);
}

type MemoryosSseUpstreamState = {
  reader: ReadableStreamDefaultReader<Uint8Array>;
  decoder: TextDecoder;
  readonly clientStopped: boolean;
  markClientStopped: () => void;
  drainThenAbort: () => Promise<void>;
};

function openMemoryosSseUpstream(
  upstream: Response,
  options?: SseStreamOptions,
): MemoryosSseUpstreamState {
  const body = upstream.body;
  if (!body) {
    throw new Error("empty_body");
  }

  const headerStreamId = upstream.headers.get("X-Stream-Id");
  if (headerStreamId) {
    options?.onStreamId?.(headerStreamId);
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  let drainFinished = false;
  let clientStopped = false;

  function markClientStopped(): void {
    clientStopped = true;
  }

  async function drainThenAbort(): Promise<void> {
    if (drainFinished) {
      return;
    }
    markClientStopped();
    drainFinished = true;
    try {
      while (true) {
        const { done } = await reader.read();
        if (done) {
          break;
        }
      }
    } catch {
      // Best-effort: keep reading so API finalize can commit interrupted assistant.
    }
    try {
      await reader.cancel();
    } catch {
      // Reader may already be closed.
    }
    options?.abortUpstream?.();
  }

  options?.onClientAbort?.(drainThenAbort);

  return {
    reader,
    decoder,
    get clientStopped() {
      return clientStopped;
    },
    markClientStopped,
    drainThenAbort,
  };
}

function handleMemoryosSseFrame(
  frame: MemoryosSseFrame,
  options?: SseStreamOptions,
): "continue" | "error" {
  if (frame.event === "error") {
    return "error";
  }

  const streamId = extractStartStreamId(frame);
  if (streamId) {
    options?.onStreamId?.(streamId);
  }

  return "continue";
}

function streamErrorFromFrame(frame: MemoryosSseFrame): Error {
  const message =
    typeof frame.data.message === "string" ? frame.data.message : "stream_error";
  return new Error(message);
}

export async function fetchMemoryosChatCompletion(
  params: UpstreamChatParams,
): Promise<Response> {
  return fetch(`${API_BASE}/api/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(params.authorization ? { Authorization: params.authorization } : {}),
    },
    body: JSON.stringify({
      conversation_id: params.conversationId,
      content: params.content,
      client_message_id: params.clientMessageId ?? undefined,
      regenerate: params.regenerate ?? false,
    }),
    signal: params.signal,
  });
}

export async function fetchMemoryosChatCancel(
  params: UpstreamCancelParams,
): Promise<Response> {
  return fetch(`${API_BASE}/api/v1/chat/completions/cancel`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(params.authorization ? { Authorization: params.authorization } : {}),
    },
    body: JSON.stringify({
      stream_id: params.streamId,
      visible_content: params.visibleContent ?? undefined,
      visible_length: params.visibleLength ?? undefined,
    }),
  });
}

/** 将 MemoryOS SSE 帧转为 AI SDK TextStream 所需的纯文本流。 */
export function memoryosSseResponseToTextStream(
  upstream: Response,
  options?: SseStreamOptions,
): ReadableStream<Uint8Array> {
  const state = openMemoryosSseUpstream(upstream, options);
  const encoder = new TextEncoder();
  let buffer = "";

  return new ReadableStream<Uint8Array>({
    async pull(controller) {
      if (state.clientStopped) {
        controller.close();
        return;
      }

      const { done, value } = await state.reader.read();
      if (value) {
        buffer += state.decoder.decode(value, { stream: true });
      }

      const blocks = buffer.split("\n\n");
      buffer = done ? "" : (blocks.pop() ?? "");

      for (const block of blocks) {
        if (state.clientStopped) {
          controller.close();
          return;
        }

        for (const line of block.split("\n")) {
          const frame = parseSseDataLine(line);
          if (!frame) {
            continue;
          }
          if (handleMemoryosSseFrame(frame, options) === "error") {
            controller.error(streamErrorFromFrame(frame));
            return;
          }

          const token = extractTokenContent(frame);
          if (token && !state.clientStopped) {
            controller.enqueue(encoder.encode(token));
          }
        }
      }

      if (done) {
        controller.close();
      }
    },
    cancel() {
      void state.drainThenAbort();
    },
  });
}

/** 将 MemoryOS SSE 帧转为 AI SDK DefaultChatTransport 所需的 UI message stream（SSE JSON 帧）。 */
export function memoryosSseResponseToDataStream(
  upstream: Response,
  options?: SseStreamOptions,
): ReadableStream<Uint8Array> {
  const state = openMemoryosSseUpstream(upstream, options);
  let buffer = "";
  let streamInitialized = false;
  let textStarted = false;
  let streamFinalized = false;

  let pendingTokenText = "";
  let pullEmitCount = 0;

  function enqueuePart(
    controller: ReadableStreamDefaultController<Uint8Array>,
    part: MemoryosUiDataStreamPart,
  ): void {
    if (state.clientStopped || streamFinalized) {
      return;
    }
    pullEmitCount += 1;
    controller.enqueue(encodeUiMessageStreamPart(part));
  }

  function initializeStream(
    controller: ReadableStreamDefaultController<Uint8Array>,
  ): void {
    if (streamInitialized) {
      return;
    }
    streamInitialized = true;
    enqueuePart(controller, { type: "start" });
    enqueuePart(controller, { type: "start-step" });
  }

  function endTextStreamIfOpen(
    controller: ReadableStreamDefaultController<Uint8Array>,
  ): void {
    if (!textStarted) {
      return;
    }
    enqueuePart(controller, {
      type: "text-end",
      id: UI_MESSAGE_TEXT_PART_ID,
    });
    textStarted = false;
  }

  function enqueueRagSources(
    controller: ReadableStreamDefaultController<Uint8Array>,
    items: RagSourceItem[],
  ): void {
    flushPendingTokenDelta(controller);
    initializeStream(controller);
    endTextStreamIfOpen(controller);
    enqueuePart(controller, {
      type: RAG_SOURCES_UI_DATA_TYPE,
      data: { items },
    });
  }

  function enqueueToolCall(
    controller: ReadableStreamDefaultController<Uint8Array>,
    payload: ToolCallPayload,
  ): void {
    flushPendingTokenDelta(controller);
    initializeStream(controller);
    endTextStreamIfOpen(controller);
    enqueuePart(controller, {
      type: TOOL_CALL_UI_DATA_TYPE,
      data: payload,
    });
  }

  function enqueueToolResult(
    controller: ReadableStreamDefaultController<Uint8Array>,
    payload: ToolResultPayload,
  ): void {
    flushPendingTokenDelta(controller);
    initializeStream(controller);
    endTextStreamIfOpen(controller);
    enqueuePart(controller, {
      type: TOOL_RESULT_UI_DATA_TYPE,
      data: payload,
    });
  }

  function enqueueTokenDelta(
    controller: ReadableStreamDefaultController<Uint8Array>,
    token: string,
  ): void {
    initializeStream(controller);
    if (!textStarted) {
      enqueuePart(controller, {
        type: "text-start",
        id: UI_MESSAGE_TEXT_PART_ID,
      });
      textStarted = true;
    }
    enqueuePart(controller, {
      type: "text-delta",
      id: UI_MESSAGE_TEXT_PART_ID,
      delta: token,
    });
  }

  function finalizeStream(
    controller: ReadableStreamDefaultController<Uint8Array>,
    donePayload: MemoryosDonePayload | null,
  ): void {
    if (streamFinalized || state.clientStopped) {
      return;
    }
    flushPendingTokenDelta(controller);
    if (!streamInitialized) {
      initializeStream(controller);
    }
    if (textStarted) {
      enqueuePart(controller, {
        type: "text-end",
        id: UI_MESSAGE_TEXT_PART_ID,
      });
    }
    if (donePayload) {
      enqueuePart(controller, {
        type: "message-metadata",
        messageMetadata: {
          messageId: donePayload.message_id,
          ...(donePayload.sources
            ? { ragSources: donePayload.sources }
            : {}),
        },
      });
    }
    enqueuePart(controller, { type: "finish-step" });
    enqueuePart(controller, { type: "finish" });
    streamFinalized = true;
    controller.enqueue(new TextEncoder().encode(UI_MESSAGE_STREAM_DONE));
    controller.close();
  }

  function flushPendingTokenDelta(
    controller: ReadableStreamDefaultController<Uint8Array>,
  ): void {
    if (!pendingTokenText) {
      return;
    }
    const batch = pendingTokenText;
    pendingTokenText = "";
    enqueueTokenDelta(controller, batch);
  }

  function appendToken(
    controller: ReadableStreamDefaultController<Uint8Array>,
    token: string,
  ): void {
    pendingTokenText += token;
    if (pendingTokenText.length >= TOKEN_COALESCE_MIN_CHARS) {
      flushPendingTokenDelta(controller);
    }
  }

  function processBufferedFrames(
    controller: ReadableStreamDefaultController<Uint8Array>,
    blocks: string[],
  ): boolean {
    for (const block of blocks) {
      if (state.clientStopped) {
        controller.close();
        return true;
      }

      for (const line of block.split("\n")) {
        const frame = parseSseDataLine(line);
        if (!frame) {
          continue;
        }
        if (handleMemoryosSseFrame(frame, options) === "error") {
          controller.error(streamErrorFromFrame(frame));
          return true;
        }

        const sources = extractSourcesItems(frame);
        if (sources) {
          enqueueRagSources(controller, sources);
          continue;
        }

        const toolCall = extractToolCallPayload(frame);
        if (toolCall) {
          enqueueToolCall(controller, toolCall);
          continue;
        }

        const toolResult = extractToolResultPayload(frame);
        if (toolResult) {
          enqueueToolResult(controller, toolResult);
          continue;
        }

        const token = extractTokenContent(frame);
        if (token) {
          appendToken(controller, token);
          continue;
        }

        const donePayload = extractDonePayload(frame);
        if (donePayload) {
          finalizeStream(controller, donePayload);
          return true;
        }
      }
    }
    return false;
  }

  return new ReadableStream<Uint8Array>({
    async pull(controller) {
      if (state.clientStopped || streamFinalized) {
        if (!streamFinalized) {
          controller.close();
        }
        return;
      }

      pullEmitCount = 0;

      while (true) {
        if (state.clientStopped || streamFinalized) {
          return;
        }

        const emitCountBefore = pullEmitCount;
        const { done, value } = await state.reader.read();
        if (value) {
          buffer += state.decoder.decode(value, { stream: true });
        }

        const blocks = buffer.split("\n\n");
        buffer = done ? "" : (blocks.pop() ?? "");

        if (processBufferedFrames(controller, blocks)) {
          return;
        }

        if (
          pendingTokenText.length >= TOKEN_COALESCE_MIN_CHARS &&
          pullEmitCount === emitCountBefore
        ) {
          flushPendingTokenDelta(controller);
        }

        if (pullEmitCount > emitCountBefore) {
          return;
        }

        if (done) {
          finalizeStream(controller, null);
          return;
        }
      }
    },
    cancel() {
      void state.drainThenAbort();
    },
  });
}
