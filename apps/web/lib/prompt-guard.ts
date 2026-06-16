import { createGuard } from "llm-prompt-guard";

export type BffPromptGuardMode = "tag" | "quarantine";

export type BffPromptGuardResult =
  | { action: "forward"; content: string }
  | { action: "reject"; code: 42201; message: "prompt_injection_detected" };

function isPromptGuardEnabled(): boolean {
  return process.env.BFF_PROMPT_GUARD_ENABLED === "true";
}

function promptGuardMode(): BffPromptGuardMode {
  const raw = process.env.BFF_PROMPT_GUARD_MODE?.toLowerCase();
  return raw === "quarantine" ? "quarantine" : "tag";
}

function promptGuardMaxLength(): number {
  const parsed = Number(process.env.BFF_CHAT_MAX_CONTENT_CHARS ?? "200");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 200;
}

/** BFF early feedback; API remains authoritative for direct calls. */
export function evaluateBffPromptGuard(content: string): BffPromptGuardResult {
  if (!isPromptGuardEnabled()) {
    return { action: "forward", content };
  }

  const guard = createGuard();
  const maxLength = promptGuardMaxLength();
  const mode = promptGuardMode();

  if (mode === "tag") {
    guard.sanitize(content, {
      maxLength,
      mode: "tag",
      fieldName: "userMessage",
    });
    return { action: "forward", content };
  }

  const result = guard.sanitize(content, {
    maxLength,
    mode: "block",
    fieldName: "userMessage",
  });
  if (result.wasBlocked) {
    return {
      action: "reject",
      code: 42201,
      message: "prompt_injection_detected",
    };
  }
  return { action: "forward", content };
}
