import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type {
  GitHubConnectResult,
  GitHubIntegration,
  GitHubPullRequestLink,
  GitHubStatusAutomation,
} from "./types";

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

export async function listGitHubAutomations(
  workspaceId: string,
): Promise<GitHubStatusAutomation[]> {
  const { data } = await httpClient.get<DataEnvelope<GitHubStatusAutomation[]>>(
    `/workspaces/${workspaceId}/integrations/github/automations`,
  );
  return data.data;
}

export async function setGitHubAutomation(
  workspaceId: string,
  rule: GitHubStatusAutomation,
): Promise<GitHubStatusAutomation[]> {
  const { data } = await httpClient.put<DataEnvelope<GitHubStatusAutomation[]>>(
    `/workspaces/${workspaceId}/integrations/github/automations`,
    rule,
  );
  return data.data;
}
