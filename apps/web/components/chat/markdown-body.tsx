"use client";

import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import { MarkdownErrorBoundary } from "@/components/chat/markdown-error-boundary";
import { safeMarkdownHref } from "@/lib/safe-markdown-href";

import "highlight.js/styles/github.css";

const RAG_SOURCES_HEADING = "## 参考来源";

type MarkdownBodyProps = {
  content: string;
};

const markdownComponents: Components = {
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
      <table className="min-w-full border-collapse text-xs">{children}</table>
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
};

const ragSourcesComponents: Components = {
  ...markdownComponents,
  ul: ({ children }) => (
    <ul className="list-disc space-y-1 pl-4 last:mb-0">{children}</ul>
  ),
  li: ({ children }) => <li className="leading-snug">{children}</li>,
};

function splitRagSourcesSection(content: string): {
  body: string;
  sourcesMarkdown: string | null;
} {
  const lines = content.split("\n");
  const headingIndex = lines.findIndex(
    (line) => line.trim() === RAG_SOURCES_HEADING,
  );
  if (headingIndex === -1) {
    return { body: content, sourcesMarkdown: null };
  }

  const body = lines.slice(0, headingIndex).join("\n").trimEnd();
  const sourcesMarkdown = lines.slice(headingIndex + 1).join("\n").trim();
  return {
    body,
    sourcesMarkdown: sourcesMarkdown || null,
  };
}

function MarkdownBlock({
  content,
  components = markdownComponents,
}: {
  content: string;
  components?: Components;
}) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight]}
      components={components}
    >
      {content}
    </ReactMarkdown>
  );
}

export function MarkdownBody({ content }: MarkdownBodyProps) {
  const { body, sourcesMarkdown } = splitRagSourcesSection(content);
  const plainFallback = (
    <p className="whitespace-pre-wrap text-zinc-500">{content}</p>
  );

  return (
    <div className="message-markdown text-sm leading-relaxed">
      <MarkdownErrorBoundary key={content} fallback={plainFallback}>
        {body ? <MarkdownBlock content={body} /> : null}
        {sourcesMarkdown ? (
          <details className="rag-sources mt-3 border-t border-zinc-200 pt-2 dark:border-zinc-800">
            <summary className="cursor-pointer text-xs font-medium text-zinc-500 select-none hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300">
              参考来源
            </summary>
            <div className="mt-2 text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
              <MarkdownBlock
                content={sourcesMarkdown}
                components={ragSourcesComponents}
              />
            </div>
          </details>
        ) : null}
      </MarkdownErrorBoundary>
    </div>
  );
}
