import Link from "next/link";

/** EP02 将实现完整聊天 UI，此处为占位页 */
export default function ChatPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6">
      <h1 className="text-2xl font-semibold">对话模块</h1>
      <p className="text-zinc-500">将在 EP02 实现流式对话与多轮会话</p>
      <Link href="/" className="text-sm text-emerald-600 hover:underline">
        ← 返回首页
      </Link>
    </div>
  );
}
