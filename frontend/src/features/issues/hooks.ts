import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { IssueCreateInput, IssueListParams, IssueUpdateInput } from "./types";

function issuesListKey(workspaceId: string, params: IssueListParams) {
  return ["workspaces", workspaceId, "issues", params] as const;
}

function issueKey(workspaceId: string, issueId: string) {
  return ["workspaces", workspaceId, "issues", "detail", issueId] as const;
}

function issueActivityKey(workspaceId: string, issueId: string) {
  return ["workspaces", workspaceId, "issues", "activity", issueId] as const;
}

export function useIssues(workspaceId: string, params: IssueListParams) {
  return useQuery({
    queryKey: issuesListKey(workspaceId, params),
    queryFn: () => api.listIssues(workspaceId, params),
    enabled: Boolean(workspaceId),
    placeholderData: keepPreviousData,
  });
}

export function useIssue(workspaceId: string, issueId: string) {
  return useQuery({
    queryKey: issueKey(workspaceId, issueId),
    queryFn: () => api.getIssue(workspaceId, issueId),
    enabled: Boolean(workspaceId && issueId),
  });
}

export function useIssueActivity(workspaceId: string, issueId: string) {
  return useQuery({
    queryKey: issueActivityKey(workspaceId, issueId),
    queryFn: () => api.listIssueActivity(workspaceId, issueId),
    enabled: Boolean(workspaceId && issueId),
  });
}

function useInvalidateIssues(workspaceId: string) {
  const queryClient = useQueryClient();
  return (issueId?: string) => {
    queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "issues"] });
    if (issueId) {
      queryClient.invalidateQueries({ queryKey: issueKey(workspaceId, issueId) });
      queryClient.invalidateQueries({ queryKey: issueActivityKey(workspaceId, issueId) });
    }
  };
}

export function useCreateIssue(workspaceId: string) {
  const invalidate = useInvalidateIssues(workspaceId);
  return useMutation({
    mutationFn: (input: IssueCreateInput) => api.createIssue(workspaceId, input),
    onSuccess: () => {
      invalidate();
      toast.success("Issue criada.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateIssue(workspaceId: string, issueId: string) {
  const invalidate = useInvalidateIssues(workspaceId);
  return useMutation({
    mutationFn: (input: IssueUpdateInput) => api.updateIssue(workspaceId, issueId, input),
    onSuccess: () => {
      invalidate(issueId);
      toast.success("Issue atualizada.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteIssue(workspaceId: string) {
  const invalidate = useInvalidateIssues(workspaceId);
  return useMutation({
    mutationFn: (issueId: string) => api.deleteIssue(workspaceId, issueId),
    onSuccess: () => {
      invalidate();
      toast.success("Issue excluída.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
