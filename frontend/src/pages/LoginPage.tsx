import { Navigate, useLocation } from "react-router-dom";

import { LoginForm } from "@/features/auth/components/LoginForm";
import { AuthLayout } from "@/shared/components/layout/AuthLayout";
import { resolveLoginRedirect } from "@/shared/lib/routes";
import { useAuthStore } from "@/shared/stores/authStore";

export function LoginPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const location = useLocation();
  const redirectTo = resolveLoginRedirect(location.state);

  if (accessToken) {
    return <Navigate to={redirectTo} replace />;
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-sm">
        <LoginForm redirectTo={redirectTo} />
      </div>
    </AuthLayout>
  );
}
