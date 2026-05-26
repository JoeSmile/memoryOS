"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";
import { setAccessToken } from "@/lib/auth-token";

type UserRead = {
  id: string;
  email: string;
};

type TokenData = {
  access_token: string;
  token_type: string;
};

export function RegisterForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("两次输入的密码不一致");
      return;
    }

    setLoading(true);
    try {
      await apiFetch<UserRead>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      const loginRes = await apiFetch<TokenData>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (!loginRes.data?.access_token) {
        setError("注册成功，但自动登录失败，请手动登录");
        router.push("/login");
        return;
      }

      setAccessToken(loginRes.data.access_token);
      router.push("/chat");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === 40901 || err.message === "email_already_exists") {
          setError("该邮箱已被注册");
        } else {
          setError(err.message);
        }
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
        <h1 className="text-xl font-semibold">注册</h1>
        <p className="text-sm text-zinc-500">创建 MemoryOS 账号</p>
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
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950"
        />
        <span className="text-xs text-zinc-500">8–128 位</span>
      </label>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">确认密码</span>
        <input
          type="password"
          name="confirmPassword"
          required
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
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
        {loading ? "注册中…" : "注册并登录"}
      </button>

      <p className="text-center text-sm text-zinc-500">
        已有账号？{" "}
        <Link href="/login" className="text-emerald-600 hover:underline">
          去登录
        </Link>
      </p>
    </form>
  );
}
