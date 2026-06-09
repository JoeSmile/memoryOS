import type { UIMessage } from "ai";

import { type RagSourceItem } from "@/lib/sse-frames";

export type { RagSourceItem };

/** AI SDK custom data part type for structured RAG citations (matches BFF converter). */
export const RAG_SOURCES_DATA_PART_TYPE = "data-rag-sources" as const;

export type RagSourcesDataPart = {
  type: typeof RAG_SOURCES_DATA_PART_TYPE;
  data: { items: RagSourceItem[] };
};

export type ChatUIDataTypes = {
  "rag-sources": { items: RagSourceItem[] };
};

export type ChatMessageMetadata = {
  completionStatus?: string | null;
  ragSources?: RagSourceItem[];
};

export type ChatUIMessage = UIMessage<
  ChatMessageMetadata,
  ChatUIDataTypes
>;

export type UserRead = {
  id: string;
  email: string;
};

export type ConversationRead = {
  id: string;
  title: string;
};

export type MessageMetadataRead = {
  rag_sources?: RagSourceItem[];
};

export type MessageRead = {
  id: string;
  role: string;
  content: string;
  client_message_id?: string | null;
  completion_status?: string | null;
  metadata?: MessageMetadataRead | null;
  created_at: string;
};

export const COMPLETION_INTERRUPTED = "interrupted";

function isRagSourceItem(value: unknown): value is RagSourceItem {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const row = value as Record<string, unknown>;
  return (
    typeof row.external_id === "string" &&
    row.external_id.length > 0 &&
    typeof row.collection === "string" &&
    row.collection.length > 0 &&
    typeof row.score === "number" &&
    !Number.isNaN(row.score) &&
    typeof row.content_preview === "string"
  );
}

export function parseRagSourcesFromMetadata(
  metadata: unknown,
): RagSourceItem[] | null {
  if (typeof metadata !== "object" || metadata === null) {
    return null;
  }
  const sources = (metadata as MessageMetadataRead).rag_sources;
  if (!Array.isArray(sources) || sources.length === 0) {
    return null;
  }
  if (!sources.every(isRagSourceItem)) {
    return null;
  }
  return sources;
}

export function getRagSourcesFromMessageRead(
  row: MessageRead,
): RagSourceItem[] | null {
  return parseRagSourcesFromMetadata(row.metadata);
}

export function getCompletionStatus(message: UIMessage): string | null {
  const metadata = message.metadata as ChatMessageMetadata | undefined;
  return metadata?.completionStatus ?? null;
}

export function getTextFromUIMessage(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("");
}

export function getRagSourcesFromUIMessage(
  message: UIMessage,
): RagSourceItem[] | null {
  for (const part of message.parts) {
    if (part.type !== RAG_SOURCES_DATA_PART_TYPE) {
      continue;
    }
    const data = (part as RagSourcesDataPart).data;
    const items = data.items.filter(isRagSourceItem);
    if (items.length > 0) {
      return items;
    }
  }

  const metadata = message.metadata as ChatMessageMetadata | undefined;
  if (metadata?.ragSources?.length) {
    return metadata.ragSources;
  }

  return null;
}

export function toUIMessages(rows: MessageRead[]): ChatUIMessage[] {
  return rows.map((row) => {
    const ragSources = getRagSourcesFromMessageRead(row);
    const parts: ChatUIMessage["parts"] = [
      { type: "text", text: row.content },
    ];
    if (ragSources) {
      parts.unshift({
        type: RAG_SOURCES_DATA_PART_TYPE,
        data: { items: ragSources },
      });
    }

    const metadata: ChatMessageMetadata = {};
    if (row.completion_status) {
      metadata.completionStatus = row.completion_status;
    }
    if (ragSources) {
      metadata.ragSources = ragSources;
    }

    return {
      id: row.id,
      role: row.role === "assistant" ? "assistant" : "user",
      parts,
      metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
    };
  });
}

/** 用于判断服务端消息列表是否变化，避免重复 setMessages 触发死循环。 */
export function messagesFingerprint(rows: MessageRead[]): string {
  return rows
    .map((m) => {
      const rag = getRagSourcesFromMessageRead(m)
        ?.map((item) => item.external_id)
        .join(",") ?? "";
      return `${m.id}:${m.role}:${m.content}:${m.completion_status ?? ""}:${rag}`;
    })
    .join("|");
}

export const EMPTY_MESSAGES: MessageRead[] = [];
