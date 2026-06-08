export type MemoryosSseFrame = {
  event: string;
  data: Record<string, unknown>;
};

/** Aligns with FastAPI chat SSE `sources.data.items` / `done.data.sources`. */
export type RagSourceItem = {
  external_id: string;
  collection: string;
  entity_type?: string | null;
  score: number;
  content_preview: string;
};

export type MemoryosDonePayload = {
  message_id: string;
  stream_id?: string;
  sources?: RagSourceItem[];
};

export function parseSseDataLine(line: string): MemoryosSseFrame | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith("data:")) {
    return null;
  }
  try {
    return JSON.parse(trimmed.slice(5).trim()) as MemoryosSseFrame;
  } catch {
    return null;
  }
}

function parseRagSourceItem(value: unknown): RagSourceItem | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const row = value as Record<string, unknown>;
  const externalId = row.external_id;
  const collection = row.collection;
  const score = row.score;
  const contentPreview = row.content_preview;
  if (typeof externalId !== "string" || externalId.length === 0) {
    return null;
  }
  if (typeof collection !== "string" || collection.length === 0) {
    return null;
  }
  if (typeof score !== "number" || Number.isNaN(score)) {
    return null;
  }
  if (typeof contentPreview !== "string") {
    return null;
  }
  const entityType = row.entity_type;
  return {
    external_id: externalId,
    collection,
    score,
    content_preview: contentPreview,
    ...(entityType === null || typeof entityType === "string"
      ? { entity_type: entityType }
      : {}),
  };
}

function parseRagSourceItems(value: unknown): RagSourceItem[] | null {
  if (!Array.isArray(value) || value.length === 0) {
    return null;
  }
  const items: RagSourceItem[] = [];
  for (const entry of value) {
    const parsed = parseRagSourceItem(entry);
    if (parsed === null) {
      return null;
    }
    items.push(parsed);
  }
  return items;
}

export function extractTokenContent(frame: MemoryosSseFrame): string | null {
  if (frame.event !== "token") {
    return null;
  }
  const content = frame.data.content;
  return typeof content === "string" && content.length > 0 ? content : null;
}

export function extractStartStreamId(frame: MemoryosSseFrame): string | null {
  if (frame.event !== "start") {
    return null;
  }
  const streamId = frame.data.stream_id;
  return typeof streamId === "string" && streamId.length > 0 ? streamId : null;
}

export function extractSourcesItems(frame: MemoryosSseFrame): RagSourceItem[] | null {
  if (frame.event !== "sources") {
    return null;
  }
  return parseRagSourceItems(frame.data.items);
}

export function extractDonePayload(frame: MemoryosSseFrame): MemoryosDonePayload | null {
  if (frame.event !== "done") {
    return null;
  }
  const messageId = frame.data.message_id;
  if (typeof messageId !== "string" || messageId.length === 0) {
    return null;
  }
  const payload: MemoryosDonePayload = { message_id: messageId };
  const streamId = frame.data.stream_id;
  if (typeof streamId === "string" && streamId.length > 0) {
    payload.stream_id = streamId;
  }
  const sources = frame.data.sources;
  if (sources !== undefined) {
    const parsed = parseRagSourceItems(sources);
    if (parsed !== null) {
      payload.sources = parsed;
    }
  }
  return payload;
}
