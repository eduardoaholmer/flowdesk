import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { PermissionOverrideUpsertInput } from "./types";

function permissionMatrixKey(workspaceId: string) {
  return ["workspaces", workspaceId, "permission-overrides"] as const;
}

export function usePermissionMatrix(workspaceId: string) {
  return useQuery({
    queryKey: permissionMatrixKey(workspaceId),
    queryFn: () => api.listPermissionMatrix(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 30_000,
  });
}

export function useSetPermissionOverride(workspaceId: string) {
  const queryClient = useQueryClient();
  const key = permissionMatrixKey(workspaceId);

  return useMutation({
    mutationFn: (input: PermissionOverrideUpsertInput) =>
      api.setPermissionOverride(workspaceId, input),
    onSuccess: (matrix) => {
      // A resposta já é a matriz inteira recalculada — substitui o cache
      // direto em vez de invalidar e esperar um refetch (mesma resposta).
      queryClient.setQueryData(key, matrix);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
