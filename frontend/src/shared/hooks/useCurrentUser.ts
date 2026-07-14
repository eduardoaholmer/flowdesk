import { useQuery } from "@tanstack/react-query";

import type { DataEnvelope } from "@/shared/lib/apiTypes";
import { httpClient } from "@/shared/lib/httpClient";
import { useAuthStore } from "@/shared/stores/authStore";
import type { UserProfile } from "@/features/auth/types";

/**
 * Perfil do usuário autenticado + suas memberships de workspace — fonte única
 * usada tanto para o roteamento (`/` decide para onde ir a partir de
 * `workspaces`) quanto para resolver `useWorkspace()` a partir do slug na URL.
 */
export function useCurrentUser() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ["users", "me"],
    queryFn: async () => {
      const { data } = await httpClient.get<DataEnvelope<UserProfile>>("/users/me");
      return data.data;
    },
    enabled: Boolean(accessToken),
    staleTime: 60_000,
  });
}
