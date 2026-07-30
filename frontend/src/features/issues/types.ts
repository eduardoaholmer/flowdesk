export type IssuePriority = "NO_PRIORITY" | "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export interface Issue {
  id: string;
  workspace_id: string;
  project_id: string | null;
  identifier: string;
  number: number;
  title: string;
  description: string | null;
  status_id: string;
  priority: IssuePriority;
  assignee_id: string | null;
  creator_id: string;
  estimate: number | null;
  due_date: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export type IssueSort =
  | "number"
  | "-number"
  | "created_at"
  | "-created_at"
  | "updated_at"
  | "-updated_at"
  | "priority"
  | "-priority"
  | "due_date"
  | "-due_date";

export interface IssueListParams {
  page: number;
  per_page: number;
  q?: string;
  status_id?: string;
  priority?: IssuePriority;
  project_id?: string;
  assignee_id?: string;
  creator_id?: string;
  sort?: IssueSort;
}

export interface IssueCreateInput {
  title: string;
  description?: string;
  project_id?: string;
  status_id?: string;
  priority?: IssuePriority;
  assignee_id?: string;
  estimate?: number;
  due_date?: string | null;
}

export type IssueUpdateInput = Partial<IssueCreateInput>;

export interface IssueActivityLogEntry {
  id: string;
  issue_id: string;
  actor_id: string;
  action: string;
  field: string | null;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}
