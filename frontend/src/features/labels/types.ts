export interface Label {
  id: string;
  workspace_id: string;
  name: string;
  color: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface LabelCreateInput {
  name: string;
  color: string;
  description?: string;
}

export type LabelUpdateInput = Partial<LabelCreateInput>;
