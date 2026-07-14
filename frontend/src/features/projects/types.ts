export type ProjectStatus = "ACTIVE" | "ARCHIVED";

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  status: ProjectStatus;
  target_date: string | null;
  lead_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type ProjectSort =
  | "name"
  | "-name"
  | "created_at"
  | "-created_at"
  | "updated_at"
  | "-updated_at"
  | "target_date"
  | "-target_date";

export interface ProjectListParams {
  page: number;
  per_page: number;
  search?: string;
  status?: ProjectStatus;
  sort?: ProjectSort;
}

export interface ProjectCreateInput {
  name: string;
  slug?: string;
  description?: string;
  icon?: string;
  color?: string;
}

export type ProjectUpdateInput = Partial<ProjectCreateInput>;
