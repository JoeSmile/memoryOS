"use client";

import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import { MarkdownErrorBoundary } from "@/components/chat/markdown-error-boundary";
import { safeMarkdownHref } from "@/lib/safe-markdown-href";

import "highlight.js/styles/github.css";

type MarkdownBodyProps = {
  content: string;
};

export function MarkdownBody({ content }: MarkdownBodyProps) {
  const plainFallback = (
    <p className="whitespace-pre-wrap text-zinc-500">{content}</p>
  );

  return (
    <div className="message-markdown text-sm leading-relaxed">
      <MarkdownErrorBoundary key={content} fallback={plainFallback}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight]}
          components={{
            p: ({ children }) => (
              <p className="mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="mb-2 list-disc pl-5 last:mb-0">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="mb-2 list-decimal pl-5 last:mb-0">{children}</ol>
            ),
            li: ({ children }) => <li className="mb-0.5">{children}</li>,
            a: ({ href, children }) => {
              const safeHref = safeMarkdownHref(href);
              if (!safeHref) {
                return <span className="text-emerald-600">{children}</span>;
              }
              return (
                <a
                  href={safeHref}
                  className="text-emerald-600 underline hover:opacity-80 dark:text-emerald-400"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {children}
                </a>
              );
            },
            blockquote: ({ children }) => (
              <blockquote className="mb-2 border-l-2 border-zinc-300 pl-3 text-zinc-600 last:mb-0 dark:border-zinc-600 dark:text-zinc-400">
                {children}
              </blockquote>
            ),
            pre: ({ children }) => (
              <pre className="mb-2 overflow-x-auto rounded-lg bg-zinc-100 p-3 text-xs last:mb-0 dark:bg-zinc-900">
                {children}
              </pre>
            ),
            code: ({ className, children }) => {
              const isBlock = Boolean(className?.includes("language-"));
              if (isBlock) {
                return <code className={className}>{children}</code>;
              }
              return (
                <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs dark:bg-zinc-800">
                  {children}
                </code>
              );
            },
            table: ({ children }) => (
              <div className="mb-2 overflow-x-auto last:mb-0">
                <table className="min-w-full border-collapse text-xs">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="border border-zinc-200 bg-zinc-50 px-2 py-1 text-left dark:border-zinc-700 dark:bg-zinc-900">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-zinc-200 px-2 py-1 dark:border-zinc-700">
                {children}
              </td>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </MarkdownErrorBoundary>
    </div>
  );
}
