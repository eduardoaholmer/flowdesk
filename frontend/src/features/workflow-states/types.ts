export type WorkflowStateCategory = "BACKLOG" | "UNSTARTED" | "STARTED" | "COMPLETED" | "CANCELED";

export interface WorkflowState {
  id: string;
  workspace_id: string;
  name: string;
  category: WorkflowStateCategory;
  position: number;
  is_default: boolean;
  issue_count: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowStateCreateInput {
  name: string;
  category: WorkflowStateCategory;
  is_default?: boolean;
}

export type WorkflowStateUpdateInput = Partial<WorkflowStateCreateInput>;
