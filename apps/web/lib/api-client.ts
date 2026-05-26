import {
  clearAccessToken,
  getAccessToken,
} from "@/lib/auth-token";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ApiEnvelope<T> = {
  code: number;
  message: string;
  data: T | null;
};

export class ApiError extends Error {
  constructor(
    public readonly code: number,
    message: string,
    public readonly httpStatus: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * 统一 fetch：自动附加 Bearer；已登录时 401 清 token 并跳转 /login。
 */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  let body: ApiEnvelope<T>;
  try {
    body = (await res.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError(res.status, "invalid_json", res.status);
  }

  if (res.status === 401 && token) {
    clearAccessToken();
    if (
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login")
    ) {
      window.location.assign("/login");
    }
  }

  if (!res.ok || body.code !== 0) {
    throw new ApiError(
      body.code ?? res.status,
      body.message ?? "request_failed",
      res.status,
    );
  }

  return body;
}
