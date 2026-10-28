import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { takeGitHubConnectWorkspace } from "@/features/github/connectReturn";
import { workspaceRoutes } from "@/shared/lib/routes";

const ERROR_MESSAGES: Record<string, string> = {
  github_connect_state_invalid:
    "A conexão com o GitHub expirou ou foi iniciada em outro navegador. Tente novamente.",
  github_authorization_failed:
    "Não foi possível confirmar a autorização com o GitHub. Tente novamente.",
  github_installation_not_accessible: "Sua conta do GitHub não tem acesso a esta instalação.",
  github_installation_already_connected:
    "Esta conta do GitHub já está conectada a outro workspace.",
  github_integration_not_configured: "A integração com GitHub não está disponível.",
  permission_denied: "Você não tem permissão para gerenciar integrações neste workspace.",
};
const DEFAULT_ERROR_MESSAGE = "Não foi possível conectar o GitHub. Tente novamente.";
const PENDING_APPROVAL_CODE = "github_installation_pending_approval";

/**
 * Destino do redirect que o backend emite ao fim da instalação do GitHub App
 * (`GET /integrations/github/setup`). Só traduz o resultado em toast e volta à
 * aba Integrações do workspace de onde a conexão partiu.
 */
export function GitHubCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const ranOnce = useRef(false);

  useEffect(() => {
    if (ranOnce.current) return;
    ranOnce.current = true;

    const errorCode = searchParams.get("error");
    if (errorCode === PENDING_APPROVAL_CODE) {
      toast.info(
        "A instalação aguarda aprovação de um dono da organização no GitHub. Depois de aprovada, conecte de novo.",
      );
    } else if (errorCode) {
      toast.error(ERROR_MESSAGES[errorCode] ?? DEFAULT_ERROR_MESSAGE);
    } else {
      toast.success("GitHub conectado.");
    }

    const workspaceSlug = takeGitHubConnectWorkspace();
    navigate(workspaceSlug ? `${workspaceRoutes.settings(workspaceSlug)}?tab=integrations` : "/", {
      replace: true,
    });
  }, [navigate, searchParams]);

  return (
    <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
      Conectando o GitHub…
    </div>
  );
}
