import type { AuthUser } from "@/features/auth/types";
import type { Invitation } from "@/features/workspaces/types";
import type { Issue } from "@/features/issues/types";
import type { Notification } from "@/features/notifications/types";
import type { Project } from "@/features/projects/types";
import type { WorkspaceMember } from "@/features/workspaces/types";
import type { PaginationMeta } from "@/shared/lib/apiTypes";

export const demoUser: AuthUser = {
  id: "user-1",
  name: "Ada Lovelace",
  email: "ada@example.com",
  avatar_url: null,
  created_at: "2026-01-01T00:00:00Z",
};

export const demoProject: Project = {
  id: "project-1",
  workspace_id: "workspace-1",
  name: "Núcleo de Issues",
  slug: "nucleo-de-issues",
  description: null,
  icon: null,
  color: null,
  status: "ACTIVE",
  target_date: null,
  lead_id: null,
  created_by: "user-1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

export const demoIssue: Issue = {
  id: "issue-1",
  workspace_id: "workspace-1",
  project_id: "project-1",
  identifier: "FLW-1",
  number: 1,
  title: "Configurar infraestrutura de mock de rede",
  description: null,
  status: "TODO",
  priority: "MEDIUM",
  assignee_id: "user-1",
  creator_id: "user-1",
  estimate: null,
  due_date: null,
  version: 1,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

export const demoNotification: Notification = {
  id: "notification-1",
  workspace_id: "workspace-1",
  type: "ASSIGNMENT",
  payload: {
    issue_id: "issue-1",
    issue_identifier: "FLW-1",
    actor_name: "Ada Lovelace",
  },
  read_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

export const demoMember: WorkspaceMember = {
  id: "member-1",
  workspace_id: "workspace-1",
  role: "MEMBER",
  status: "ACTIVE",
  joined_at: "2026-01-01T00:00:00Z",
  user: {
    id: "user-1",
    name: "Ada Lovelace",
    email: "ada@example.com",
    avatar_url: null,
  },
};

export const demoInvitation: Invitation = {
  id: "invitation-1",
  workspace_id: "workspace-1",
  email: "grace@example.com",
  role: "MEMBER",
  status: "PENDING",
  invited_by_id: "user-1",
  expires_at: "2026-01-08T00:00:00Z",
  created_at: "2026-01-01T00:00:00Z",
};

export function buildPaginationMeta(page: number, perPage: number, total: number): PaginationMeta {
  return {
    page,
    per_page: perPage,
    total,
    total_pages: Math.max(1, Math.ceil(total / perPage)),
  };
}
