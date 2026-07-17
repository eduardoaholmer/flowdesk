import { Navigate } from "react-router-dom";

import { ForgotPasswordForm } from "@/features/auth/components/ForgotPasswordForm";
import { Logo } from "@/shared/components/brand/Logo";
import { AuthLayout } from "@/shared/components/layout/AuthLayout";
import { useAuthStore } from "@/shared/stores/authStore";

export function ForgotPasswordPage() {
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
        <p className="mb-6 text-sm text-muted-foreground">
          Informe seu e-mail para receber um link de redefinição de senha.
        </p>
        <ForgotPasswordForm />
      </div>
    </AuthLayout>
  );
}
