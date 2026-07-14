import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { LabelCreateInput, LabelUpdateInput } from "./types";

function labelsListKey(workspaceId: string) {
  return ["workspaces", workspaceId, "labels"] as const;
}

function issueLabelsKey(workspaceId: string, issueId: string) {
  return ["workspaces", workspaceId, "issues", "labels", issueId] as const;
}

export function useLabels(workspaceId: string) {
  return useQuery({
    queryKey: labelsListKey(workspaceId),
    queryFn: () => api.listLabels(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 30_000,
  });
}

export function useIssueLabels(workspaceId: string, issueId: string) {
  return useQuery({
    queryKey: issueLabelsKey(workspaceId, issueId),
    queryFn: () => api.listIssueLabels(workspaceId, issueId),
    enabled: Boolean(workspaceId && issueId),
  });
}

function useInvalidateLabels(workspaceId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: labelsListKey(workspaceId) });
  };
}

export function useCreateLabel(workspaceId: string) {
  const invalidate = useInvalidateLabels(workspaceId);
  return useMutation({
    mutationFn: (input: LabelCreateInput) => api.createLabel(workspaceId, input),
    onSuccess: () => {
      invalidate();
      toast.success("Label criada.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateLabel(workspaceId: string, labelId: string) {
  const invalidate = useInvalidateLabels(workspaceId);
  return useMutation({
    mutationFn: (input: LabelUpdateInput) => api.updateLabel(workspaceId, labelId, input),
    onSuccess: () => {
      invalidate();
      toast.success("Label atualizada.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteLabel(workspaceId: string) {
  const invalidate = useInvalidateLabels(workspaceId);
  return useMutation({
    mutationFn: (labelId: string) => api.deleteLabel(workspaceId, labelId),
    onSuccess: () => {
      invalidate();
      toast.success("Label excluída.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useAddIssueLabel(workspaceId: string, issueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (labelId: string) => api.addIssueLabel(workspaceId, issueId, labelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: issueLabelsKey(workspaceId, issueId) });
      queryClient.invalidateQueries({
        queryKey: ["workspaces", workspaceId, "issues", "activity", issueId],
      });
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useRemoveIssueLabel(workspaceId: string, issueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (labelId: string) => api.removeIssueLabel(workspaceId, issueId, labelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: issueLabelsKey(workspaceId, issueId) });
      queryClient.invalidateQueries({
        queryKey: ["workspaces", workspaceId, "issues", "activity", issueId],
      });
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
