import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";
import { httpClient } from "@/shared/lib/httpClient";
import type { CollectionEnvelope, DataEnvelope } from "@/shared/lib/apiTypes";

import type {
  Invitation,
  InvitationCreatedResult,
  InvitationCreateInput,
  InvitationListParams,
  Workspace,
  WorkspaceMember,
  WorkspaceMemberListParams,
  WorkspaceUpdateInput,
} from "./types";

export async function createWorkspace(name: string): Promise<Workspace> {
  const { data } = await httpClient.post<DataEnvelope<Workspace>>("/workspaces", { name });
  return data.data;
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  const { data } = await httpClient.get<DataEnvelope<Workspace>>(`/workspaces/${workspaceId}`);
  return data.data;
}

export async function updateWorkspace(
  workspaceId: string,
  input: WorkspaceUpdateInput,
): Promise<Workspace> {
  const { data } = await httpClient.patch<DataEnvelope<Workspace>>(
    `/workspaces/${workspaceId}`,
    input,
  );
  return data.data;
}

export async function deleteWorkspace(workspaceId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}`);
}

export async function listWorkspaceMembers(workspaceId: string): Promise<WorkspaceMember[]> {
  const { data } = await httpClient.get<CollectionEnvelope<WorkspaceMember>>(
    `/workspaces/${workspaceId}/members`,
    { params: { per_page: MAX_PICKER_PAGE_SIZE } },
  );
  return data.data;
}

/**
 * Versão paginada/filtrável de `listWorkspaceMembers`, usada pela tela de
 * administração (`WorkspaceMembersSettings`) — as demais features só precisam
 * resolver "todos os membros" para um lookup por id (atribuir issue, exibir
 * autor de comentário/anexo), sem paginação real nem filtro por papel.
 */
export async function listWorkspaceMembersPage(
  workspaceId: string,
  params: WorkspaceMemberListParams,
): Promise<CollectionEnvelope<WorkspaceMember>> {
  const { data } = await httpClient.get<CollectionEnvelope<WorkspaceMember>>(
    `/workspaces/${workspaceId}/members`,
    { params },
  );
  return data;
}

export async function updateMemberRole(
  workspaceId: string,
  memberId: string,
  role: Exclude<WorkspaceMember["role"], "OWNER">,
): Promise<WorkspaceMember> {
  const { data } = await httpClient.patch<DataEnvelope<WorkspaceMember>>(
    `/workspaces/${workspaceId}/members/${memberId}`,
    { role },
  );
  return data.data;
}

export async function removeMember(workspaceId: string, memberId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/members/${memberId}`);
}

export async function leaveWorkspace(workspaceId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/members/me`);
}

export async function listInvitations(
  workspaceId: string,
  params: InvitationListParams,
): Promise<CollectionEnvelope<Invitation>> {
  const { data } = await httpClient.get<CollectionEnvelope<Invitation>>(
    `/workspaces/${workspaceId}/invitations`,
    { params },
  );
  return data;
}

export async function createInvitation(
  workspaceId: string,
  input: InvitationCreateInput,
): Promise<InvitationCreatedResult> {
  const { data } = await httpClient.post<DataEnvelope<InvitationCreatedResult>>(
    `/workspaces/${workspaceId}/invitations`,
    input,
  );
  return data.data;
}

export async function cancelInvitation(workspaceId: string, invitationId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/invitations/${invitationId}`);
}

export async function acceptInvitation(token: string): Promise<WorkspaceMember> {
  const { data } = await httpClient.post<DataEnvelope<WorkspaceMember>>(
    `/invitations/${token}/accept`,
  );
  return data.data;
}
