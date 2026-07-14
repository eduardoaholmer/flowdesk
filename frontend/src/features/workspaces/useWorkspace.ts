import { useParams } from "react-router-dom";

import { useCurrentUser } from "@/shared/hooks/useCurrentUser";

/**
 * Resolve o workspace ativo a partir do slug na URL (`/w/:workspaceSlug/...`)
 * contra a lista de memberships do usuário (`GET /users/me`) — não existe uma
 * chamada dedicada `GET /workspaces/by-slug`, e a lista de memberships já é
 * pequena o bastante (um usuário pertence a poucos workspaces) para resolver
 * assim sem custo extra de rede.
 */
export function useWorkspace() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const { data: profile, isLoading, isError } = useCurrentUser();

  const workspace = profile?.workspaces.find((w) => w.slug === workspaceSlug) ?? null;

  return {
    workspace,
    isLoading,
    isError,
    notFound: !isLoading && !isError && workspace === null,
  };
}
