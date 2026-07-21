import { Navigate } from "react-router-dom";

import { ForgotPasswordForm } from "@/features/auth/components/ForgotPasswordForm";
import { AuthLayout } from "@/shared/components/layout/AuthLayout";
import { useAuthStore } from "@/shared/stores/authStore";

export function ForgotPasswordPage() {
  const accessToken = useAuthStore((state) => state.accessToken);

  if (accessToken) {
    return <Navigate to="/" replace />;
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <h1 className="font-heading text-2xl font-semibold tracking-tight">Redefinir senha</h1>
          <p className="mt-1.5 text-sm text-t2">Envie um link de redefinição para o seu e-mail.</p>
        </div>
        <div className="rounded-xl border border-border bg-panel p-6 shadow-sm">
          <ForgotPasswordForm />
        </div>
      </div>
    </AuthLayout>
  );
}
