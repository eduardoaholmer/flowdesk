export interface AuthUser {
  id: string;
  name: string;
  email: string;
  avatar_url: string | null;
  created_at: string;
}

export type WorkspaceRole = "OWNER" | "ADMIN" | "MEMBER" | "GUEST";

export interface WorkspaceMembershipSummary {
  id: string;
  name: string;
  slug: string;
  role: WorkspaceRole;
}

export interface UserProfile extends AuthUser {
  workspaces: WorkspaceMembershipSummary[];
}
