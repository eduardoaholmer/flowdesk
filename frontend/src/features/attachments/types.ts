export interface Attachment {
  id: string;
  workspace_id: string;
  issue_id: string | null;
  comment_id: string | null;
  uploader_id: string;
  file_name: string;
  content_type: string;
  file_size: number;
  storage_provider: string;
  created_at: string;
}
