import type { UIMessage } from "ai";
import { UI_MESSAGE_STREAM_HEADERS } from "ai";

import { getTextFromUIMessage } from "@/lib/chat-types";
import {
  fetchMemoryosChatCompletion,
  memoryosSseResponseToDataStream,
} from "@/lib/memoryos-upstream";
import { evaluateBffPromptGuard } from "@/lib/prompt-guard";

export const maxDuration = 120;

const EMPTY_UI_MESSAGE_STREAM_BODY = [
  'data: {"type":"start"}\n\n',
  'data: {"type":"start-step"}\n\n',
  'data: {"type":"finish-step"}\n\n',
  'data: {"type":"finish"}\n\n',
  "data: [DONE]\n\n",
].join("");

function uiMessageStreamResponse(
  body: BodyInit,
  extraHeaders?: Record<string, string>,
): Response {
  return new Response(body, {
    headers: {
      ...UI_MESSAGE_STREAM_HEADERS,
      ...extraHeaders,
    },
  });
}

type ChatRouteBody = {
  id?: string;
  conversation_id?: string;
  messages?: UIMessage[];
  client_message_id?: string;
  regenerate?: boolean;
};

export async function POST(req: Request) {
  const authorization = req.headers.get("authorization");
  if (!authorization?.startsWith("Bearer ")) {
    return Response.json(
      { code: 40101, message: "unauthorized", data: null },
      { status: 401 },
    );
  }

  let body: ChatRouteBody;
  try {
    body = (await req.json()) as ChatRouteBody;
  } catch {
    return Response.json(
      { code: 422, message: "invalid_json", data: null },
      { status: 422 },
    );
  }

  const conversationId = body.conversation_id ?? body.id;
  const messages = body.messages ?? [];

  if (!conversationId) {
    return Response.json(
      { code: 422, message: "conversation_id_required", data: null },
      { status: 422 },
    );
  }

  const lastUser = [...messages].reverse().find((m) => m.role === "user");
  const content = lastUser ? getTextFromUIMessage(lastUser).trim() : "";

  if (!content) {
    return Response.json(
      { code: 422, message: "content_required", data: null },
      { status: 422 },
    );
  }

  const guardResult = evaluateBffPromptGuard(content);
  if (guardResult.action === "reject") {
    return Response.json(
      {
        code: guardResult.code,
        message: guardResult.message,
        data: null,
      },
      { status: 422 },
    );
  }

  const upstreamAbort = new AbortController();
  let drainUpstreamOnClientAbort: (() => Promise<void>) | null = null;
  req.signal.addEventListener(
    "abort",
    () => {
      void drainUpstreamOnClientAbort?.();
    },
    { once: true },
  );

  const upstream = await fetchMemoryosChatCompletion({
    conversationId,
    content,
    authorization,
    signal: upstreamAbort.signal,
    clientMessageId: body.client_message_id,
    regenerate: body.regenerate ?? false,
  });

  if (!upstream.ok) {
    const errorText = await upstream.text();
    if (upstream.status === 409) {
      try {
        const payload = JSON.parse(errorText) as {
          code?: number;
          message?: string;
        };
        if (payload.code === 40902 && payload.message === "duplicate_message") {
          return uiMessageStreamResponse(EMPTY_UI_MESSAGE_STREAM_BODY, {
            "X-Chat-Duplicate": "1",
          });
        }
      } catch {
        // fall through to forward upstream error
      }
    }
    return new Response(errorText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  let streamId = upstream.headers.get("X-Stream-Id");
  const dataStream = memoryosSseResponseToDataStream(upstream, {
    onStreamId: (id) => {
      streamId = id;
    },
    onClientAbort: (drain) => {
      drainUpstreamOnClientAbort = drain;
    },
    abortUpstream: () => upstreamAbort.abort(),
  });

  const responseHeaders: Record<string, string> = {
    ...UI_MESSAGE_STREAM_HEADERS,
  };
  if (streamId) {
    responseHeaders["X-Stream-Id"] = streamId;
  }

  return new Response(dataStream, { headers: responseHeaders });
}
