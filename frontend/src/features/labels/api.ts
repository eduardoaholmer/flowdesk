import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { Label, LabelCreateInput, LabelUpdateInput } from "./types";

export async function listLabels(workspaceId: string): Promise<Label[]> {
  const { data } = await httpClient.get<DataEnvelope<Label[]>>(`/workspaces/${workspaceId}/labels`);
  return data.data;
}

export async function createLabel(workspaceId: string, input: LabelCreateInput): Promise<Label> {
  const { data } = await httpClient.post<DataEnvelope<Label>>(
    `/workspaces/${workspaceId}/labels`,
    input,
  );
  return data.data;
}

export async function updateLabel(
  workspaceId: string,
  labelId: string,
  input: LabelUpdateInput,
): Promise<Label> {
  const { data } = await httpClient.patch<DataEnvelope<Label>>(
    `/workspaces/${workspaceId}/labels/${labelId}`,
    input,
  );
  return data.data;
}

export async function deleteLabel(workspaceId: string, labelId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/labels/${labelId}`);
}

export async function listIssueLabels(workspaceId: string, issueId: string): Promise<Label[]> {
  const { data } = await httpClient.get<DataEnvelope<Label[]>>(
    `/workspaces/${workspaceId}/issues/${issueId}/labels`,
  );
  return data.data;
}

export async function addIssueLabel(
  workspaceId: string,
  issueId: string,
  labelId: string,
): Promise<Label> {
  const { data } = await httpClient.post<DataEnvelope<Label>>(
    `/workspaces/${workspaceId}/issues/${issueId}/labels`,
    { label_id: labelId },
  );
  return data.data;
}

export async function removeIssueLabel(
  workspaceId: string,
  issueId: string,
  labelId: string,
): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/issues/${issueId}/labels/${labelId}`);
}
