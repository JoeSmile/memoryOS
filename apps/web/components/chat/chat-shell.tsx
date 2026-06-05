import type { ReactNode } from "react";

type ChatShellProps = {
  header: ReactNode;
  children: ReactNode;
  footer: ReactNode;
};

export function ChatShell({ header, children, footer }: ChatShellProps) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl flex-col px-4 py-6">
      {header}
      {children}
      {footer}
    </div>
  );
}
