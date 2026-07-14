import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { CommentCreateInput, CommentListParams, CommentUpdateInput } from "./types";

function commentsListKey(workspaceId: string, issueId: string, params: CommentListParams) {
  return ["workspaces", workspaceId, "issues", "comments", issueId, params] as const;
}

function issueActivityKey(workspaceId: string, issueId: string) {
  return ["workspaces", workspaceId, "issues", "activity", issueId] as const;
}

export function useComments(workspaceId: string, issueId: string, params: CommentListParams) {
  return useQuery({
    queryKey: commentsListKey(workspaceId, issueId, params),
    queryFn: () => api.listComments(workspaceId, issueId, params),
    enabled: Boolean(workspaceId && issueId),
    placeholderData: keepPreviousData,
  });
}

function useInvalidateComments(workspaceId: string, issueId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({
      queryKey: ["workspaces", workspaceId, "issues", "comments", issueId],
    });
    queryClient.invalidateQueries({ queryKey: issueActivityKey(workspaceId, issueId) });
  };
}

export function useCreateComment(workspaceId: string, issueId: string) {
  const invalidate = useInvalidateComments(workspaceId, issueId);
  return useMutation({
    mutationFn: (input: CommentCreateInput) => api.createComment(workspaceId, issueId, input),
    onSuccess: () => invalidate(),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateComment(workspaceId: string, issueId: string, commentId: string) {
  const invalidate = useInvalidateComments(workspaceId, issueId);
  return useMutation({
    mutationFn: (input: CommentUpdateInput) => api.updateComment(workspaceId, commentId, input),
    onSuccess: () => invalidate(),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteComment(workspaceId: string, issueId: string) {
  const invalidate = useInvalidateComments(workspaceId, issueId);
  return useMutation({
    mutationFn: (commentId: string) => api.deleteComment(workspaceId, commentId),
    onSuccess: () => {
      invalidate();
      toast.success("Comentário excluído.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
