import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { GitHubConnectResult, GitHubIntegration, GitHubPullRequestLink } from "./types";

export async function getGitHubIntegration(workspaceId: string): Promise<GitHubIntegration> {
  const { data } = await httpClient.get<DataEnvelope<GitHubIntegration>>(
    `/workspaces/${workspaceId}/integrations/github`,
  );
  return data.data;
}

export async function connectGitHub(workspaceId: string): Promise<GitHubConnectResult> {
  const { data } = await httpClient.post<DataEnvelope<GitHubConnectResult>>(
    `/workspaces/${workspaceId}/integrations/github/connect`,
  );
  return data.data;
}

export async function disconnectGitHubInstallation(
  workspaceId: string,
  installationId: string,
): Promise<void> {
  await httpClient.delete(
    `/workspaces/${workspaceId}/integrations/github/installations/${installationId}`,
  );
}

export async function listIssueGitHubLinks(
  workspaceId: string,
  issueId: string,
): Promise<GitHubPullRequestLink[]> {
  const { data } = await httpClient.get<DataEnvelope<GitHubPullRequestLink[]>>(
    `/workspaces/${workspaceId}/issues/${issueId}/github-links`,
  );
  return data.data;
}
