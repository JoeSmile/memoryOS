import {
  extractStartStreamId,
  extractTokenContent,
  parseSseDataLine,
} from "@/lib/sse-frames";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
};

export type SseTextStreamOptions = {
  onStreamId?: (streamId: string) => void;
  /** Called once with drain+abort; wire to req.signal so Stop keeps upstream open until drained. */
  onClientAbort?: (drain: () => Promise<void>) => void;
  abortUpstream?: () => void;
};

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
    }),
  });
}

/** 将 MemoryOS SSE 帧转为 AI SDK TextStream 所需的纯文本流。 */
export function memoryosSseResponseToTextStream(
  upstream: Response,
  options?: SseTextStreamOptions,
): ReadableStream<Uint8Array> {
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
  const encoder = new TextEncoder();
  let buffer = "";

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

  return new ReadableStream<Uint8Array>({
    async pull(controller) {
      if (clientStopped) {
        controller.close();
        return;
      }

      while (true) {
        if (clientStopped) {
          controller.close();
          return;
        }

        const { done, value } = await reader.read();
        if (done) {
          controller.close();
          return;
        }

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";

        for (const block of blocks) {
          if (clientStopped) {
            controller.close();
            return;
          }

          for (const line of block.split("\n")) {
            const frame = parseSseDataLine(line);
            if (!frame) {
              continue;
            }
            if (frame.event === "error") {
              const message =
                typeof frame.data.message === "string"
                  ? frame.data.message
                  : "stream_error";
              controller.error(new Error(message));
              return;
            }

            const streamId = extractStartStreamId(frame);
            if (streamId) {
              options?.onStreamId?.(streamId);
            }

            const token = extractTokenContent(frame);
            if (token && !clientStopped) {
              controller.enqueue(encoder.encode(token));
            }
          }
        }
      }
    },
    cancel() {
      void drainThenAbort();
    },
  });
}
