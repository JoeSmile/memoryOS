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

/** Aligns with FastAPI chat SSE `tool_call.data`. */
export type ToolCallPayload = {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
};

/** Aligns with FastAPI chat SSE `tool_result.data` / persisted `metadata.tool_steps`. */
export type ToolResultPayload = {
  id: string;
  name: string;
  success: boolean;
  summary: string;
  duration_ms?: number;
  error?: string;
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

function parsePlainObject(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function parseToolCallData(data: Record<string, unknown>): ToolCallPayload | null {
  const id = data.id;
  const name = data.name;
  if (typeof id !== "string" || id.length === 0) {
    return null;
  }
  if (typeof name !== "string" || name.length === 0) {
    return null;
  }
  const argsRaw = data.arguments;
  if (argsRaw === undefined) {
    return { id, name, arguments: {} };
  }
  const arguments_ = parsePlainObject(argsRaw);
  if (arguments_ === null) {
    return null;
  }
  return { id, name, arguments: arguments_ };
}

function parseToolResultData(data: Record<string, unknown>): ToolResultPayload | null {
  const id = data.id;
  const name = data.name;
  const success = data.success;
  const summary = data.summary;
  if (typeof id !== "string" || id.length === 0) {
    return null;
  }
  if (typeof name !== "string" || name.length === 0) {
    return null;
  }
  if (typeof success !== "boolean") {
    return null;
  }
  if (typeof summary !== "string") {
    return null;
  }
  const payload: ToolResultPayload = { id, name, success, summary };
  const durationMs = data.duration_ms;
  if (typeof durationMs === "number" && Number.isFinite(durationMs)) {
    payload.duration_ms = durationMs;
  }
  const error = data.error;
  if (typeof error === "string" && error.length > 0) {
    payload.error = error;
  }
  return payload;
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

export function extractToolCallPayload(
  frame: MemoryosSseFrame,
): ToolCallPayload | null {
  if (frame.event !== "tool_call") {
    return null;
  }
  return parseToolCallData(frame.data);
}

export function extractToolResultPayload(
  frame: MemoryosSseFrame,
): ToolResultPayload | null {
  if (frame.event !== "tool_result") {
    return null;
  }
  return parseToolResultData(frame.data);
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
