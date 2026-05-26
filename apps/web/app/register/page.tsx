import type { Metadata } from "next";

import { RegisterForm } from "@/components/register-form";

export const metadata: Metadata = {
  title: "注册",
};

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-16">
      <RegisterForm />
    </div>
  );
}
