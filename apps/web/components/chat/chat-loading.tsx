type ChatLoadingProps = {
  label?: string;
};

export function ChatLoading({ label = "加载对话…" }: ChatLoadingProps) {
  return (
    <div className="flex min-h-screen items-center justify-center text-sm text-zinc-500">
      {label}
    </div>
  );
}
