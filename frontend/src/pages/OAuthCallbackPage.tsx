import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { refreshAccessToken } from "@/shared/lib/httpClient";

const ERROR_MESSAGES: Record<string, string> = {
  oauth_authentication_failed: "Não foi possível concluir o login social. Tente novamente.",
  oauth_provider_not_configured: "Este provedor de login não está disponível.",
};
const DEFAULT_ERROR_MESSAGE = "Não foi possível concluir o login social. Tente novamente.";

/**
 * Destino do redirect que o backend emite ao final do Authorization Code flow
 * (`GET /auth/{provider}/callback`) — nunca chega access token na URL (CLAUDE.md
 * §11): sucesso só deixa os cookies de sessão prontos, e é `refreshAccessToken`
 * (mesma função que `AuthBootstrap` usa após um reload) quem troca isso por um
 * access token em memória.
 */
export function OAuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const ranOnce = useRef(false);

  useEffect(() => {
    if (ranOnce.current) return;
    ranOnce.current = true;

    const errorCode = searchParams.get("error");
    if (errorCode) {
      toast.error(ERROR_MESSAGES[errorCode] ?? DEFAULT_ERROR_MESSAGE);
      navigate("/login", { replace: true });
      return;
    }

    refreshAccessToken()
      .then(() => {
        navigate("/", { replace: true });
      })
      .catch(() => {
        toast.error(DEFAULT_ERROR_MESSAGE);
        navigate("/login", { replace: true });
      });
  }, [navigate, searchParams]);

  return (
    <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
      Entrando…
    </div>
  );
}
