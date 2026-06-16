import { FormEvent } from "react";

type ChatComposerProps = {
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
  /** LLM SSE active — shows Stop (not used for demo-turn / pre-stream wait). */
  isStreaming: boolean;
  /** Demo-turn or pre-stream send — disables input + Send, does not show Stop. */
  isSending?: boolean;
  onStop: () => void;
  disabled?: boolean;
  errorMessage?: string | null;
  onRetry?: () => void;
};

export function ChatComposer({
  input,
  onInputChange,
  onSubmit,
  isStreaming,
  isSending = false,
  onStop,
  disabled = false,
  errorMessage = null,
  onRetry,
}: ChatComposerProps) {
  const inputLocked = disabled || isSending || isStreaming;
  const sendLocked = disabled || isSending || !input.trim();
  return (
    <div className="shrink-0 border-t border-zinc-200 pt-4 dark:border-zinc-800 relative z-10 bg-[var(--background)]">
      {errorMessage ? (
        <div
          className="mb-2 flex flex-wrap items-center gap-2 text-sm text-red-600 dark:text-red-400"
          role="alert"
        >
          <span>{errorMessage}</span>
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="rounded border border-red-300 px-2 py-0.5 text-xs hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-950/40"
            >
              重试
            </button>
          ) : null}
        </div>
      ) : null}

      <form
        onSubmit={onSubmit}
        className="flex gap-2"
        aria-busy={isSending || isStreaming ? "true" : undefined}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder="输入消息…"
          disabled={inputLocked}
          className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={onStop}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            停止
          </button>
        ) : (
          <button
            type="submit"
            disabled={sendLocked}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            发送
          </button>
        )}
      </form>
    </div>
  );
}
