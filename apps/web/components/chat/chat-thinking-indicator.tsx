type ChatThinkingIndicatorProps = {
  label?: string;
};

export function ChatThinkingIndicator({
  label = "思考中…",
}: ChatThinkingIndicatorProps) {
  return (
    <div
      className="mr-8 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm dark:border-zinc-800 dark:bg-zinc-950"
      aria-live="polite"
      aria-busy="true"
      data-testid="chat-thinking-indicator"
    >
      <p className="mb-1 text-xs font-medium uppercase tracking-wide opacity-60">
        助手
      </p>
      <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
        <span className="inline-flex gap-1" aria-hidden>
          <span
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500 [animation-delay:-0.3s]"
          />
          <span
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500 [animation-delay:-0.15s]"
          />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 dark:bg-zinc-500" />
        </span>
        <span className="text-sm">{label}</span>
      </div>
    </div>
  );
}
