import { httpClient } from "@/shared/lib/httpClient";
import type { CollectionEnvelope, DataEnvelope } from "@/shared/lib/apiTypes";

import type { Project, ProjectCreateInput, ProjectListParams, ProjectUpdateInput } from "./types";

export async function listProjects(
  workspaceId: string,
  params: ProjectListParams,
): Promise<CollectionEnvelope<Project>> {
  const { data } = await httpClient.get<CollectionEnvelope<Project>>(
    `/workspaces/${workspaceId}/projects`,
    { params },
  );
  return data;
}

export async function getProject(workspaceId: string, projectId: string): Promise<Project> {
  const { data } = await httpClient.get<DataEnvelope<Project>>(
    `/workspaces/${workspaceId}/projects/${projectId}`,
  );
  return data.data;
}

export async function createProject(
  workspaceId: string,
  input: ProjectCreateInput,
): Promise<Project> {
  const { data } = await httpClient.post<DataEnvelope<Project>>(
    `/workspaces/${workspaceId}/projects`,
    input,
  );
  return data.data;
}

export async function updateProject(
  workspaceId: string,
  projectId: string,
  input: ProjectUpdateInput,
): Promise<Project> {
  const { data } = await httpClient.patch<DataEnvelope<Project>>(
    `/workspaces/${workspaceId}/projects/${projectId}`,
    input,
  );
  return data.data;
}

export async function archiveProject(workspaceId: string, projectId: string): Promise<Project> {
  const { data } = await httpClient.post<DataEnvelope<Project>>(
    `/workspaces/${workspaceId}/projects/${projectId}/archive`,
  );
  return data.data;
}

export async function restoreProject(workspaceId: string, projectId: string): Promise<Project> {
  const { data } = await httpClient.post<DataEnvelope<Project>>(
    `/workspaces/${workspaceId}/projects/${projectId}/restore`,
  );
  return data.data;
}

export async function deleteProject(workspaceId: string, projectId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/projects/${projectId}`);
}
