import Link from "next/link";

type ChatHeaderProps = {
  title?: string;
  loadedMessageCount?: number;
};

export function ChatHeader({
  title = "分析对话",
  loadedMessageCount = 0,
}: ChatHeaderProps) {
  return (
    <header className="mb-4 flex shrink-0 items-start justify-between border-b border-zinc-200 pb-4 dark:border-zinc-800">
      <div>
        <h1 className="text-lg font-semibold">{title}</h1>
        <p className="text-xs text-zinc-500">单会话 · 连续追问</p>
        {loadedMessageCount > 0 ? (
          <p className="mt-1 text-xs text-zinc-500">
            {loadedMessageCount} 条消息已载入上下文
            <span className="opacity-70"> · 完整裁剪在后端</span>
          </p>
        ) : null}
      </div>
      <Link href="/" className="text-sm text-emerald-600 hover:underline">
        首页
      </Link>
    </header>
  );
}
