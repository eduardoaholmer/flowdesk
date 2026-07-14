export interface Comment {
  id: string;
  workspace_id: string;
  issue_id: string;
  author_id: string;
  body: string;
  mentioned_user_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface CommentCreateInput {
  body: string;
}

export interface CommentUpdateInput {
  body: string;
}

export interface CommentListParams {
  page: number;
  per_page: number;
}
