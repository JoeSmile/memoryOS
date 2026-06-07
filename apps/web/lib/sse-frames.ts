export type MemoryosSseFrame = {
  event: string;
  data: Record<string, unknown>;
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
