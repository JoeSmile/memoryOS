import {
  extractTokenContent,
  parseSseDataLine,
  type MemoryosSseFrame,
} from "@/lib/sse-frames";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ChatDoneData = {
  message_id: string;
  stream_id: string;
};

export type StreamChatHandlers = {
  onToken: (content: string) => void;
  onDone: (data: ChatDoneData) => void;
  onError: (message: string) => void;
};

export type StreamChatParams = {
  conversationId: string;
  content: string;
  token: string;
  signal?: AbortSignal;
} & StreamChatHandlers;

function dispatchFrame(frame: MemoryosSseFrame, handlers: StreamChatHandlers): void {
  const token = extractTokenContent(frame);
  if (token) {
    handlers.onToken(token);
    return;
  }

  if (frame.event === "done") {
    handlers.onDone({
      message_id: String(frame.data.message_id ?? ""),
      stream_id: String(frame.data.stream_id ?? ""),
    });
    return;
  }

  if (frame.event === "error") {
    const message =
      typeof frame.data.message === "string"
        ? frame.data.message
        : "stream_error";
    handlers.onError(message);
  }
}

/**
 * 直连 FastAPI SSE（保留供测试或非 useChat 场景）。
 * 聊天页默认走 `/api/chat` + Vercel AI SDK `useChat`。
 */
export async function streamChatCompletion(
  params: StreamChatParams,
): Promise<void> {
  const { conversationId, content, token, signal, ...handlers } = params;

  const res = await fetch(`${API_BASE}/api/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      content,
    }),
    signal,
  });

  if (!res.ok) {
    let message = "request_failed";
    try {
      const body = (await res.json()) as { message?: string };
      message = body.message ?? message;
    } catch {
      // non-JSON error body
    }
    handlers.onError(message);
    return;
  }

  const body = res.body;
  if (!body) {
    handlers.onError("empty_body");
    return;
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";

      for (const block of blocks) {
        for (const line of block.split("\n")) {
          const frame = parseSseDataLine(line);
          if (frame) {
            dispatchFrame(frame, handlers);
          }
        }
      }
    }
  } catch (err) {
    if (signal?.aborted) {
      return;
    }
    const message = err instanceof Error ? err.message : "stream_interrupted";
    handlers.onError(message);
  }
}
