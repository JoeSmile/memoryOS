"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";
import { setAccessToken } from "@/lib/auth-token";

type TokenData = {
  access_token: string;
  token_type: string;
};

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiFetch<TokenData>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (!res.data?.access_token) {
        setError("登录响应异常");
        return;
      }
      setAccessToken(res.data.access_token);
      router.push("/chat");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message === "invalid_credentials" ? "邮箱或密码错误" : err.message);
      } else {
        setError("网络错误，请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-sm space-y-4 rounded-xl border border-zinc-200 p-6 dark:border-zinc-800"
    >
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">登录</h1>
        <p className="text-sm text-zinc-500">使用注册邮箱登录 MemoryOS</p>
      </div>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">邮箱</span>
        <input
          type="email"
          name="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
        />
      </label>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">密码</span>
        <input
          type="password"
          name="password"
          required
          minLength={8}
          maxLength={128}
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
        />
      </label>

      {error ? (
        <p className="text-sm text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-zinc-900 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        {loading ? "登录中…" : "登录"}
      </button>

      <p className="text-center text-sm text-zinc-500">
        还没有账号？{" "}
        <Link href="/register" className="text-emerald-600 hover:underline">
          去注册
        </Link>
        {" · "}
        <Link href="/" className="text-emerald-600 hover:underline">
          返回首页
        </Link>
      </p>
    </form>
  );
}
