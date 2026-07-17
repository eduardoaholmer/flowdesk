export type NotificationType = "MENTION" | "ASSIGNMENT" | "STATUS_CHANGE";

export interface MentionPayload {
  issue_id: string;
  issue_identifier: string;
  comment_id: string;
  actor_name: string;
  preview: string;
}

export interface StatusChangePayload {
  issue_id: string;
  issue_identifier: string;
  actor_name: string;
  old_status: string;
  new_status: string;
}

export interface Notification {
  id: string;
  workspace_id: string;
  type: NotificationType;
  payload: Partial<MentionPayload & StatusChangePayload> & Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}
