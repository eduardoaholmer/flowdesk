import { useEffect, type ReactNode } from "react";

import { isAuthRejection, refreshAccessToken } from "@/shared/lib/httpClient";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { useAuthStore } from "@/shared/stores/authStore";

/**
 * O access token some a cada reload (vive só em memória, CLAUDE.md §11) — na
 * carga inicial da SPA, tenta reobter um novo a partir do refresh token em
 * cookie `HttpOnly`. Duas saídas bem diferentes (docs/09-decision-log.md ADR-062):
 * um 401/422 real do backend significa "sem sessão válida", e a aplicação segue
 * normalmente para `/login` (`RequireAuth` cuida do redirecionamento). Qualquer
 * outra falha (timeout, rede fora do ar, backend indisponível) NÃO significa
 * "deslogado" — é mostrado um estado de erro explícito com "tentar novamente",
 * nunca um loading infinito nem um logout silencioso por uma instabilidade alheia
 * à sessão do usuário.
 */
export function AuthBootstrap({ children }: { children: ReactNode }) {
  const bootstrapStatus = useAuthStore((state) => state.bootstrapStatus);
  const setBootstrapped = useAuthStore((state) => state.setBootstrapped);
  const setBootstrapError = useAuthStore((state) => state.setBootstrapError);
  const retryBootstrap = useAuthStore((state) => state.retryBootstrap);

  useEffect(() => {
    if (bootstrapStatus !== "initializing") return;

    let cancelled = false;

    refreshAccessToken()
      .then(() => {
        if (!cancelled) setBootstrapped();
      })
      .catch((error) => {
        if (cancelled) return;
        if (isAuthRejection(error)) {
          setBootstrapped();
        } else {
          setBootstrapError();
        }
      });

    return () => {
      cancelled = true;
    };
  }, [bootstrapStatus, setBootstrapped, setBootstrapError]);

  if (bootstrapStatus === "error") {
    return (
      <div className="flex h-screen items-center justify-center p-6">
        <ErrorState
          message="Não foi possível carregar o FlowDesk. Verifique sua conexão ou tente novamente."
          onRetry={retryBootstrap}
        />
      </div>
    );
  }

  if (bootstrapStatus === "initializing") {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Carregando…
      </div>
    );
  }

  return <>{children}</>;
}
