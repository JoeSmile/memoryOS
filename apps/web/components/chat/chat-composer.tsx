import { FormEvent } from "react";

type ChatComposerProps = {
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
  isStreaming: boolean;
  onStop: () => void;
  disabled?: boolean;
  errorMessage?: string | null;
};

export function ChatComposer({
  input,
  onInputChange,
  onSubmit,
  isStreaming,
  onStop,
  disabled = false,
  errorMessage = null,
}: ChatComposerProps) {
  return (
    <div className="shrink-0 border-t border-zinc-200 pt-4 dark:border-zinc-800">
      {errorMessage ? (
        <p className="mb-2 text-sm text-red-600 dark:text-red-400" role="alert">
          {errorMessage}
        </p>
      ) : null}

      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder="输入消息…"
          disabled={disabled || isStreaming}
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
            disabled={disabled || !input.trim()}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            发送
          </button>
        )}
      </form>
    </div>
  );
}
