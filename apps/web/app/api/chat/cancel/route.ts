import { fetchMemoryosChatCancel } from "@/lib/memoryos-upstream";

export const maxDuration = 60;

type CancelRouteBody = {
  stream_id?: string;
  visible_content?: string;
  visible_length?: number;
};

export async function POST(req: Request) {
  const authorization = req.headers.get("authorization");
  if (!authorization?.startsWith("Bearer ")) {
    return Response.json(
      { code: 40101, message: "unauthorized", data: null },
      { status: 401 },
    );
  }

  let body: CancelRouteBody;
  try {
    body = (await req.json()) as CancelRouteBody;
  } catch {
    return Response.json(
      { code: 422, message: "invalid_json", data: null },
      { status: 422 },
    );
  }

  const streamId = body.stream_id?.trim();
  if (!streamId) {
    return Response.json(
      { code: 422, message: "stream_id_required", data: null },
      { status: 422 },
    );
  }

  const upstream = await fetchMemoryosChatCancel({
    streamId,
    authorization,
    visibleContent: body.visible_content ?? null,
    visibleLength: body.visible_length ?? null,
  });
  const text = await upstream.text();

  return new Response(text, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
