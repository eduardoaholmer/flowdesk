import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";
import { httpClient } from "@/shared/lib/httpClient";
import type { CollectionEnvelope, DataEnvelope } from "@/shared/lib/apiTypes";

import type { Workspace, WorkspaceMember } from "./types";

export async function createWorkspace(name: string): Promise<Workspace> {
  const { data } = await httpClient.post<DataEnvelope<Workspace>>("/workspaces", { name });
  return data.data;
}

export async function listWorkspaceMembers(workspaceId: string): Promise<WorkspaceMember[]> {
  const { data } = await httpClient.get<CollectionEnvelope<WorkspaceMember>>(
    `/workspaces/${workspaceId}/members`,
    { params: { per_page: MAX_PICKER_PAGE_SIZE } },
  );
  return data.data;
}
