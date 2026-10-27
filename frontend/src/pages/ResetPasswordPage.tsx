import { Navigate, useParams } from "react-router-dom";

import { ResetPasswordForm } from "@/features/auth/components/ResetPasswordForm";
import { AuthLayout } from "@/shared/components/layout/AuthLayout";
import { useAuthStore } from "@/shared/stores/authStore";

export function ResetPasswordPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const { token } = useParams<{ token: string }>();

  if (accessToken) {
    return <Navigate to="/" replace />;
  }
  if (!token) {
    return <Navigate to="/forgot-password" replace />;
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
            Escolha uma nova senha
          </h1>
          <p className="mt-1.5 text-sm text-t2">Para a conta acessada por este link.</p>
        </div>
        <div className="rounded-xl border border-border bg-panel p-6 shadow-sm">
          <ResetPasswordForm token={token} />
        </div>
      </div>
    </AuthLayout>
  );
}
