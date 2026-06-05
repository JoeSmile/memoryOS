import type { UIMessage } from "ai";

import { getTextFromUIMessage } from "@/lib/chat-types";
import {
  fetchMemoryosChatCompletion,
  memoryosSseResponseToTextStream,
} from "@/lib/memoryos-upstream";

export const maxDuration = 60;

type ChatRouteBody = {
  id?: string;
  conversation_id?: string;
  messages?: UIMessage[];
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

  const upstream = await fetchMemoryosChatCompletion({
    conversationId,
    content,
    authorization,
    signal: req.signal,
  });

  if (!upstream.ok) {
    const errorText = await upstream.text();
    return new Response(errorText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  const textStream = memoryosSseResponseToTextStream(upstream);

  return new Response(textStream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
