import { useEffect, type ReactNode } from "react";

import { refreshAccessToken } from "@/shared/lib/httpClient";
import { useAuthStore } from "@/shared/stores/authStore";

/**
 * O access token some a cada reload (vive só em memória, CLAUDE.md §11) — na
 * carga inicial da SPA, tenta reobter um novo a partir do refresh token em
 * cookie `HttpOnly`. Sem sessão válida, a tentativa falha silenciosamente e o
 * usuário segue deslogado (`RequireAuth` cuida do redirecionamento).
 */
export function AuthBootstrap({ children }: { children: ReactNode }) {
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);
  const setBootstrapped = useAuthStore((state) => state.setBootstrapped);

  useEffect(() => {
    let cancelled = false;

    refreshAccessToken()
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) {
          setBootstrapped();
        }
      });

    return () => {
      cancelled = true;
    };
  }, [setBootstrapped]);

  if (isBootstrapping) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Carregando…
      </div>
    );
  }

  return <>{children}</>;
}
