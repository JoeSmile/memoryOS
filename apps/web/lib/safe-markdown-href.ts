const BLOCKED_PREFIXES = ["javascript:", "data:", "vbscript:"];

export function safeMarkdownHref(href: string | undefined): string | undefined {
  if (!href) {
    return undefined;
  }

  const trimmed = href.trim();
  const lower = trimmed.toLowerCase();

  if (BLOCKED_PREFIXES.some((prefix) => lower.startsWith(prefix))) {
    return undefined;
  }

  if (
    lower.startsWith("http://") ||
    lower.startsWith("https://") ||
    lower.startsWith("mailto:")
  ) {
    return trimmed;
  }

  if (trimmed.startsWith("/") || trimmed.startsWith("#")) {
    return trimmed;
  }

  return undefined;
}
