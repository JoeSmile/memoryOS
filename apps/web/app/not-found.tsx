import Link from "next/link";
import { APP_NAME } from "@memoryos/shared";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-6">
      <p className="text-6xl font-bold text-zinc-300 dark:text-zinc-700">404</p>
      <div className="text-center">
        <h1 className="text-xl font-semibold">页面不存在</h1>
        <p className="mt-2 text-sm text-zinc-500">
          {APP_NAME} 找不到你访问的页面
        </p>
      </div>
      <Link
        href="/"
        className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
      >
        返回首页
      </Link>
    </div>
  );
}
