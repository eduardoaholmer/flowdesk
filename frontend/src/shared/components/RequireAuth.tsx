import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "@/shared/stores/authStore";

export function RequireAuth() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
