import Link from "next/link";

type ChatHeaderProps = {
  title?: string;
  loadedMessageCount?: number;
  onNewConversation?: () => void;
  newConversationDisabled?: boolean;
};

export function ChatHeader({
  title = "分析对话",
  loadedMessageCount = 0,
  onNewConversation,
  newConversationDisabled = false,
}: ChatHeaderProps) {
  return (
    <header className="mb-4 flex shrink-0 items-start justify-between border-b border-zinc-200 pb-4 dark:border-zinc-800">
      <div>
        <h1 className="text-lg font-semibold">{title}</h1>
        <p className="text-xs text-zinc-500">单会话 · 登录后自动恢复最近一场分析</p>
        {loadedMessageCount > 0 ? (
          <p className="mt-1 text-xs text-zinc-500">
            {loadedMessageCount} 条消息在会话中
            <span className="opacity-70"> · 发送上下文裁剪在后端</span>
          </p>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-3">
        {onNewConversation ? (
          <button
            type="button"
            onClick={onNewConversation}
            disabled={newConversationDisabled}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            新建分析
          </button>
        ) : null}
        <Link href="/" className="text-sm text-emerald-600 hover:underline">
          首页
        </Link>
      </div>
    </header>
  );
}
