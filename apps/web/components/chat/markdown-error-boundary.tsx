"use client";

import { Component, type ReactNode } from "react";

type MarkdownErrorBoundaryProps = {
  children: ReactNode;
  fallback: ReactNode;
};

type MarkdownErrorBoundaryState = {
  hasError: boolean;
};

export class MarkdownErrorBoundary extends Component<
  MarkdownErrorBoundaryProps,
  MarkdownErrorBoundaryState
> {
  state: MarkdownErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): MarkdownErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    if (process.env.NODE_ENV === "development") {
      console.warn(
        "[MessageContent] Markdown render failed, falling back to plain text:",
        error,
      );
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}
