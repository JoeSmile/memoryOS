const USER_FACING_MESSAGES: Record<string, string> = {
  token_quota_exceeded: "您今日的token量使用完请过几个小时后再试",
};

export function resolveApiErrorMessage(
  code: number,
  message: string,
  data: unknown,
): string {
  if (message === "token_quota_exceeded") {
    if (
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail === "string"
    ) {
      return (data as { detail: string }).detail;
    }
    return USER_FACING_MESSAGES.token_quota_exceeded;
  }

  if (code === 42902) {
    return USER_FACING_MESSAGES.token_quota_exceeded;
  }

  return message;
}
