import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import { rememberGitHubConnectWorkspace } from "./connectReturn";

function githubIntegrationKey(workspaceId: string) {
  return ["workspaces", workspaceId, "integrations", "github"] as const;
}

export function useIssueGitHubLinks(workspaceId: string, issueId: string) {
  return useQuery({
    queryKey: ["workspaces", workspaceId, "issues", issueId, "github-links"] as const,
    queryFn: () => api.listIssueGitHubLinks(workspaceId, issueId),
    enabled: Boolean(workspaceId && issueId),
    staleTime: 30_000,
  });
}

export function useGitHubIntegration(workspaceId: string) {
  return useQuery({
    queryKey: githubIntegrationKey(workspaceId),
    queryFn: () => api.getGitHubIntegration(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 30_000,
  });
}

/** Sai da SPA para a página de instalação do GitHub App; a volta acontece por
 * `GitHubCallbackPage`. */
export function useConnectGitHub(workspaceId: string, workspaceSlug: string) {
  return useMutation({
    mutationFn: () => api.connectGitHub(workspaceId),
    onSuccess: ({ install_url }) => {
      rememberGitHubConnectWorkspace(workspaceSlug);
      window.location.assign(install_url);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDisconnectGitHubInstallation(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (installationId: string) =>
      api.disconnectGitHubInstallation(workspaceId, installationId),
    onSuccess: () => {
      toast.success("Conta do GitHub desconectada.");
      void queryClient.invalidateQueries({ queryKey: githubIntegrationKey(workspaceId) });
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
