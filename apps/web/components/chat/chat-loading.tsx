type ChatLoadingProps = {
  label?: string;
};

export function ChatLoading({ label = "加载对话…" }: ChatLoadingProps) {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-[var(--background)] text-sm text-zinc-500">
      {label}
    </div>
  );
}
