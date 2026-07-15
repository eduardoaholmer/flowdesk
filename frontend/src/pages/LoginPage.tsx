import { Navigate } from "react-router-dom";

import { LoginForm } from "@/features/auth/components/LoginForm";
import { Logo } from "@/shared/components/brand/Logo";
import { AuthLayout } from "@/shared/components/layout/AuthLayout";
import { useAuthStore } from "@/shared/stores/authStore";

export function LoginPage() {
  const accessToken = useAuthStore((state) => state.accessToken);

  if (accessToken) {
    return <Navigate to="/" replace />;
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-sm rounded-xl border p-6">
        <h1 className="mb-4">
          <Logo size="md" />
        </h1>
        <p className="mb-6 text-sm text-muted-foreground">Entre para gerenciar seus projetos.</p>
        <LoginForm />
      </div>
    </AuthLayout>
  );
}
