import type { ReactNode } from "react";

type ChatShellProps = {
  header: ReactNode;
  children: ReactNode;
  footer: ReactNode;
};

export function ChatShell({ header, children, footer }: ChatShellProps) {
  return (
    <div className="mx-auto flex h-screen max-h-dvh w-full max-w-3xl flex-col overflow-hidden px-4 py-6">
      {header}
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      {footer}
    </div>
  );
}
