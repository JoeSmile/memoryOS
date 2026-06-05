import type { UIMessage } from "ai";

export type UserRead = {
  id: string;
  email: string;
};

export type ConversationRead = {
  id: string;
  title: string;
};

export type MessageRead = {
  id: string;
  role: string;
  content: string;
  created_at: string;
};

export function getTextFromUIMessage(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("");
}

export function toUIMessages(rows: MessageRead[]): UIMessage[] {
  return rows.map((row) => ({
    id: row.id,
    role: row.role === "assistant" ? "assistant" : "user",
    parts: [{ type: "text" as const, text: row.content }],
  }));
}

/** 用于判断服务端消息列表是否变化，避免重复 setMessages 触发死循环。 */
export function messagesFingerprint(rows: MessageRead[]): string {
  return rows.map((m) => `${m.id}:${m.role}:${m.content}`).join("|");
}

export const EMPTY_MESSAGES: MessageRead[] = [];
