import type { UIMessage } from "ai";

import {
  type RagSourceItem,
  type ToolCallPayload,
  type ToolResultPayload,
} from "@/lib/sse-frames";

export type { RagSourceItem, ToolCallPayload, ToolResultPayload };

/** AI SDK custom data part type for structured RAG citations (matches BFF converter). */
export const RAG_SOURCES_DATA_PART_TYPE = "data-rag-sources" as const;

/** AI SDK custom data parts for Unified ReAct tool rounds (matches BFF converter). */
export const TOOL_CALL_DATA_PART_TYPE = "data-tool-call" as const;
export const TOOL_RESULT_DATA_PART_TYPE = "data-tool-result" as const;

/** Persisted ReAct tool round (`metadata.tool_steps` item); aligns with API `ToolStepRead`. */
export type ToolStepItem = {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  success: boolean;
  summary: string;
  duration_ms?: number;
};

export type RagSourcesDataPart = {
  type: typeof RAG_SOURCES_DATA_PART_TYPE;
  data: { items: RagSourceItem[] };
};

export type ToolCallDataPart = {
  type: typeof TOOL_CALL_DATA_PART_TYPE;
  data: ToolCallPayload;
};

export type ToolResultDataPart = {
  type: typeof TOOL_RESULT_DATA_PART_TYPE;
  data: ToolResultPayload;
};

export type ChatUIDataTypes = {
  "rag-sources": { items: RagSourceItem[] };
  "tool-call": ToolCallPayload;
  "tool-result": ToolResultPayload;
};

export type ChatMessageMetadata = {
  completionStatus?: string | null;
  ragSources?: RagSourceItem[];
  toolSteps?: ToolStepItem[];
  demo?: {
    match_id?: string;
    template_id?: string;
  };
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
  updated_at?: string;
};

export type MessageMetadataRead = {
  rag_sources?: RagSourceItem[];
  tool_steps?: ToolStepItem[];
  demo?: {
    match_id?: string;
    template_id?: string;
  };
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

function parseDemoFromMetadata(metadata: unknown): ChatMessageMetadata["demo"] {
  if (typeof metadata !== "object" || metadata === null) {
    return undefined;
  }
  const demo = (metadata as MessageMetadataRead).demo;
  if (typeof demo !== "object" || demo === null) {
    return undefined;
  }
  return {
    match_id:
      typeof demo.match_id === "string" ? demo.match_id : undefined,
    template_id:
      typeof demo.template_id === "string" ? demo.template_id : undefined,
  };
}

export function isDemoMessageRead(row: MessageRead): boolean {
  return parseDemoFromMetadata(row.metadata) !== undefined;
}

export function isDemoUIMessage(message: UIMessage): boolean {
  const metadata = message.metadata as ChatMessageMetadata | undefined;
  if (metadata?.demo) {
    return true;
  }
  return parseDemoFromMetadata(metadata) !== undefined;
}

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

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isToolStepItem(value: unknown): value is ToolStepItem {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const row = value as Record<string, unknown>;
  if (
    typeof row.id !== "string" ||
    row.id.length === 0 ||
    typeof row.name !== "string" ||
    row.name.length === 0 ||
    typeof row.success !== "boolean" ||
    typeof row.summary !== "string"
  ) {
    return false;
  }
  const args = row.arguments;
  if (args !== undefined && !isPlainObject(args)) {
    return false;
  }
  const durationMs = row.duration_ms;
  if (
    durationMs !== undefined &&
    (typeof durationMs !== "number" || !Number.isFinite(durationMs))
  ) {
    return false;
  }
  return true;
}

export function parseToolStepsFromMetadata(
  metadata: unknown,
): ToolStepItem[] | null {
  if (typeof metadata !== "object" || metadata === null) {
    return null;
  }
  const steps = (metadata as MessageMetadataRead).tool_steps;
  if (!Array.isArray(steps) || steps.length === 0) {
    return null;
  }
  if (!steps.every(isToolStepItem)) {
    return null;
  }
  return steps.map((step) => ({
    ...step,
    arguments: step.arguments ?? {},
  }));
}

export function getToolStepsFromMessageRead(
  row: MessageRead,
): ToolStepItem[] | null {
  return parseToolStepsFromMetadata(row.metadata);
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

function mergeToolStepFromParts(
  call: ToolCallPayload,
  result: ToolResultPayload,
): ToolStepItem {
  return {
    id: result.id,
    name: result.name,
    arguments: call.arguments,
    success: result.success,
    summary: result.summary,
    ...(result.duration_ms != null ? { duration_ms: result.duration_ms } : {}),
  };
}

export function getToolStepsFromUIMessage(
  message: UIMessage,
): ToolStepItem[] | null {
  const pendingCalls = new Map<string, ToolCallPayload>();
  const steps: ToolStepItem[] = [];

  for (const part of message.parts) {
    if (part.type === TOOL_CALL_DATA_PART_TYPE) {
      const data = (part as ToolCallDataPart).data;
      if (typeof data.id === "string" && data.id.length > 0) {
        pendingCalls.set(data.id, data);
      }
      continue;
    }
    if (part.type !== TOOL_RESULT_DATA_PART_TYPE) {
      continue;
    }
    const data = (part as ToolResultDataPart).data;
    if (typeof data.id !== "string" || data.id.length === 0) {
      continue;
    }
    const call = pendingCalls.get(data.id);
    steps.push(
      mergeToolStepFromParts(
        call ?? { id: data.id, name: data.name, arguments: {} },
        data,
      ),
    );
    pendingCalls.delete(data.id);
  }

  if (steps.length > 0) {
    return steps;
  }

  const metadata = message.metadata as ChatMessageMetadata | undefined;
  if (metadata?.toolSteps?.length) {
    return metadata.toolSteps;
  }

  return null;
}

function buildToolStepDataParts(steps: ToolStepItem[]): ChatUIMessage["parts"] {
  const parts: ChatUIMessage["parts"] = [];
  for (const step of steps) {
    parts.push({
      type: TOOL_CALL_DATA_PART_TYPE,
      data: {
        id: step.id,
        name: step.name,
        arguments: step.arguments,
      },
    });
    parts.push({
      type: TOOL_RESULT_DATA_PART_TYPE,
      data: {
        id: step.id,
        name: step.name,
        success: step.success,
        summary: step.summary,
        ...(step.duration_ms != null ? { duration_ms: step.duration_ms } : {}),
      },
    });
  }
  return parts;
}

export function toUIMessages(rows: MessageRead[]): ChatUIMessage[] {
  return rows.map((row) => {
    const ragSources = getRagSourcesFromMessageRead(row);
    const toolSteps = getToolStepsFromMessageRead(row);
    const parts: ChatUIMessage["parts"] = [
      { type: "text", text: row.content },
    ];
    if (toolSteps) {
      parts.unshift(...buildToolStepDataParts(toolSteps));
    }
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
    if (toolSteps) {
      metadata.toolSteps = toolSteps;
    }
    const demo = parseDemoFromMetadata(row.metadata);
    if (demo) {
      metadata.demo = demo;
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
      const tools =
        getToolStepsFromMessageRead(m)
          ?.map((step) => step.id)
          .join(",") ?? "";
      return `${m.id}:${m.role}:${m.content}:${m.completion_status ?? ""}:${rag}:${tools}`;
    })
    .join("|");
}

export const EMPTY_MESSAGES: MessageRead[] = [];
