"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";

const MarkdownBody = dynamic(
  () =>
    import("@/components/chat/markdown-body").then((mod) => mod.MarkdownBody),
  { ssr: false },
);

type MessageContentProps = {
  content: string;
  /** Assistant messages use Markdown after streaming completes. */
  markdown?: boolean;
};

export function MessageContent({
  content,
  markdown = false,
}: MessageContentProps) {
  if (!markdown) {
    return <p className="whitespace-pre-wrap">{content}</p>;
  }

  return (
    <Suspense
      fallback={<p className="whitespace-pre-wrap">{content}</p>}
    >
      <MarkdownBody content={content} />
    </Suspense>
  );
}
