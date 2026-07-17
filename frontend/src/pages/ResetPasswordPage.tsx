import { Navigate, useParams } from "react-router-dom";

import { ResetPasswordForm } from "@/features/auth/components/ResetPasswordForm";
import { Logo } from "@/shared/components/brand/Logo";
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
      <div className="w-full max-w-sm rounded-xl border p-6">
        <h1 className="mb-4">
          <Logo size="md" />
        </h1>
        <p className="mb-6 text-sm text-muted-foreground">Escolha uma nova senha.</p>
        <ResetPasswordForm token={token} />
      </div>
    </AuthLayout>
  );
}
