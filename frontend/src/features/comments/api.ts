import { httpClient } from "@/shared/lib/httpClient";
import type { CollectionEnvelope, DataEnvelope } from "@/shared/lib/apiTypes";

import type { Comment, CommentCreateInput, CommentListParams, CommentUpdateInput } from "./types";

export async function listComments(
  workspaceId: string,
  issueId: string,
  params: CommentListParams,
): Promise<CollectionEnvelope<Comment>> {
  const { data } = await httpClient.get<CollectionEnvelope<Comment>>(
    `/workspaces/${workspaceId}/issues/${issueId}/comments`,
    { params },
  );
  return data;
}

export async function createComment(
  workspaceId: string,
  issueId: string,
  input: CommentCreateInput,
): Promise<Comment> {
  const { data } = await httpClient.post<DataEnvelope<Comment>>(
    `/workspaces/${workspaceId}/issues/${issueId}/comments`,
    input,
  );
  return data.data;
}

export async function updateComment(
  workspaceId: string,
  commentId: string,
  input: CommentUpdateInput,
): Promise<Comment> {
  const { data } = await httpClient.patch<DataEnvelope<Comment>>(
    `/workspaces/${workspaceId}/comments/${commentId}`,
    input,
  );
  return data.data;
}

export async function deleteComment(workspaceId: string, commentId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/comments/${commentId}`);
}
