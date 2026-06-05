import { extractTokenContent, parseSseDataLine } from "@/lib/sse-frames";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type UpstreamChatParams = {
  conversationId: string;
  content: string;
  authorization: string | null;
  signal?: AbortSignal;
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
    }),
    signal: params.signal,
  });
}

/** 将 MemoryOS SSE 帧转为 AI SDK TextStream 所需的纯文本流。 */
export function memoryosSseResponseToTextStream(
  upstream: Response,
): ReadableStream<Uint8Array> {
  const body = upstream.body;
  if (!body) {
    throw new Error("empty_body");
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  const encoder = new TextEncoder();
  let buffer = "";

  return new ReadableStream<Uint8Array>({
    async pull(controller) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          controller.close();
          return;
        }

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";

        for (const block of blocks) {
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

            const token = extractTokenContent(frame);
            if (token) {
              controller.enqueue(encoder.encode(token));
            }
          }
        }
      }
    },
    cancel() {
      void reader.cancel();
    },
  });
}
