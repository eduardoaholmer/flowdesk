import { httpClient } from "@/shared/lib/httpClient";
import type { CollectionEnvelope, DataEnvelope } from "@/shared/lib/apiTypes";

import type {
  Issue,
  IssueActivityLogEntry,
  IssueCreateInput,
  IssueListParams,
  IssueUpdateInput,
} from "./types";

export async function listIssues(
  workspaceId: string,
  params: IssueListParams,
): Promise<CollectionEnvelope<Issue>> {
  const { data } = await httpClient.get<CollectionEnvelope<Issue>>(
    `/workspaces/${workspaceId}/issues`,
    { params },
  );
  return data;
}

export async function getIssue(workspaceId: string, issueId: string): Promise<Issue> {
  const { data } = await httpClient.get<DataEnvelope<Issue>>(
    `/workspaces/${workspaceId}/issues/${issueId}`,
  );
  return data.data;
}

export async function createIssue(workspaceId: string, input: IssueCreateInput): Promise<Issue> {
  const { data } = await httpClient.post<DataEnvelope<Issue>>(
    `/workspaces/${workspaceId}/issues`,
    input,
  );
  return data.data;
}

export async function updateIssue(
  workspaceId: string,
  issueId: string,
  input: IssueUpdateInput,
): Promise<Issue> {
  const { data } = await httpClient.patch<DataEnvelope<Issue>>(
    `/workspaces/${workspaceId}/issues/${issueId}`,
    input,
  );
  return data.data;
}

export async function deleteIssue(workspaceId: string, issueId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/issues/${issueId}`);
}

export async function listIssueActivity(
  workspaceId: string,
  issueId: string,
): Promise<IssueActivityLogEntry[]> {
  const { data } = await httpClient.get<DataEnvelope<IssueActivityLogEntry[]>>(
    `/workspaces/${workspaceId}/issues/${issueId}/activity`,
  );
  return data.data;
}
