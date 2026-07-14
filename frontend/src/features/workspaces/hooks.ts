import { useQuery } from "@tanstack/react-query";

import * as api from "./api";

export function useWorkspaceMembers(workspaceId: string) {
  return useQuery({
    queryKey: ["workspaces", workspaceId, "members"],
    queryFn: () => api.listWorkspaceMembers(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 60_000,
  });
}
