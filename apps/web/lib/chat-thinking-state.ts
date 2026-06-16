import type { UIMessage } from "ai";

/**
 * Whether ChatMessageList should render the footer ChatThinkingIndicator.
 *
 * - Demo / pre-stream: isSending && !isStreaming
 * - LLM SSE before assistant row: isStreaming && last message is not assistant
 * - Streaming empty assistant bubble: false (in-bubble ThinkingPulse only)
 */
export function shouldShowListThinking(
  isSending: boolean,
  isStreaming: boolean,
  lastMessageRole: UIMessage["role"] | undefined,
): boolean {
  if (isSending && !isStreaming) {
    return true;
  }
  return isStreaming && lastMessageRole !== "assistant";
}
