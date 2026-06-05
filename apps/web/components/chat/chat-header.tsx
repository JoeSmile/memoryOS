import Link from "next/link";

type ChatHeaderProps = {
  title?: string;
  subtitle?: string;
};

export function ChatHeader({
  title = "分析对话",
  subtitle = "单会话 · 连续追问",
}: ChatHeaderProps) {
  return (
    <header className="mb-4 flex shrink-0 items-center justify-between border-b border-zinc-200 pb-4 dark:border-zinc-800">
      <div>
        <h1 className="text-lg font-semibold">{title}</h1>
        <p className="text-xs text-zinc-500">{subtitle}</p>
      </div>
      <Link href="/" className="text-sm text-emerald-600 hover:underline">
        首页
      </Link>
    </header>
  );
}
