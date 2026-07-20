import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { CollectionEnvelope } from "@/shared/lib/apiTypes";
import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type {
  Issue,
  IssueCreateInput,
  IssueListParams,
  IssueStatus,
  IssueUpdateInput,
} from "./types";

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

/**
 * Mutação dedicada ao drag-and-drop do board: diferente de `useUpdateIssue`
 * (usada pelo formulário completo de edição), aplica a mudança de coluna
 * otimisticamente no cache da lista (`listParams` precisa ser o mesmo objeto
 * passado a `useIssues` pelo board, já que a query key é derivada dele) e
 * reverte em caso de erro — sem toast de sucesso (o próprio card já se move
 * na tela) nem invalidação imediata (evita "piscar" a coluna antes do
 * `onSettled` reconciliar com o servidor).
 */
export function useMoveIssueStatus(workspaceId: string, listParams: IssueListParams) {
  const queryClient = useQueryClient();
  const key = issuesListKey(workspaceId, listParams);

  return useMutation({
    mutationFn: ({ issueId, status }: { issueId: string; status: IssueStatus }) =>
      api.updateIssue(workspaceId, issueId, { status }),
    onMutate: async ({ issueId, status }) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<CollectionEnvelope<Issue>>(key);
      if (previous) {
        queryClient.setQueryData<CollectionEnvelope<Issue>>(key, {
          ...previous,
          data: previous.data.map((issue) => (issue.id === issueId ? { ...issue, status } : issue)),
        });
      }
      return { previous };
    },
    onError: (error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(key, context.previous);
      }
      toast.error(getApiErrorMessage(error));
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "issues"] });
    },
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
