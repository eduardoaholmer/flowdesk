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
