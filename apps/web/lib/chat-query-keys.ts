export const chatQueryKeys = {
  me: ["me"] as const,
  myUsage: ["usage", "me"] as const,
  myConversations: ["conversations", "me"] as const,
  messages: (conversationId: string) => ["messages", conversationId] as const,
  memories: ["memories"] as const,
};
