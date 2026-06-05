import type { Metadata } from "next";
import { Suspense } from "react";

import { MinimalChat } from "@/components/minimal-chat";

export const metadata: Metadata = {
  title: "对话",
};

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-zinc-500">
          加载中…
        </div>
      }
    >
      <MinimalChat />
    </Suspense>
  );
}
