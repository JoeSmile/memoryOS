export const chatQueryKeys = {
  me: ["me"] as const,
  messages: (conversationId: string) => ["messages", conversationId] as const,
};
