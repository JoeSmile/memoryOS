export type MemoryType = "preference" | "fact" | "constraint";

export type MemoryRead = {
  id: string;
  user_id: string;
  memory_key: string;
  memory_type: MemoryType;
  content: string;
  importance: number;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
};

export const MEMORY_TYPE_LABELS: Record<MemoryType, string> = {
  preference: "偏好",
  fact: "事实",
  constraint: "约束",
};
