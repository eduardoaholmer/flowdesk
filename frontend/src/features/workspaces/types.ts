export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export type WorkspaceRole = "OWNER" | "ADMIN" | "MEMBER" | "GUEST";

export interface WorkspaceMember {
  id: string;
  workspace_id: string;
  role: WorkspaceRole;
  status: string;
  joined_at: string;
  user: {
    id: string;
    name: string;
    email: string;
    avatar_url: string | null;
  };
}

export interface WorkspaceUpdateInput {
  name?: string;
  slug?: string;
  description?: string;
}

export interface WorkspaceMemberListParams {
  page: number;
  per_page: number;
  role?: WorkspaceRole;
}

export type InvitationStatus = "PENDING" | "ACCEPTED" | "EXPIRED";

export interface Invitation {
  id: string;
  workspace_id: string;
  email: string;
  role: WorkspaceRole;
  status: InvitationStatus;
  invited_by_id: string;
  expires_at: string;
  created_at: string;
}

export interface InvitationCreatedResult extends Invitation {
  token: string;
}

/** `GET /invitations/{token}` — endpoint público (sem autenticação), só o
 * necessário para a tela de aceite mostrar quem convidou/para qual workspace/
 * papel antes do usuário logar ou criar conta. */
export interface InvitationPreview {
  email: string;
  role: WorkspaceRole;
  status: InvitationStatus;
  workspace_name: string;
  invited_by_name: string;
}

export interface InvitationCreateInput {
  email: string;
  role: Exclude<WorkspaceRole, "OWNER">;
}

export interface InvitationListParams {
  page: number;
  per_page: number;
}
