import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { WorkflowStateCreateInput, WorkflowStateUpdateInput } from "./types";

function workflowStatesKey(workspaceId: string) {
  return ["workspaces", workspaceId, "workflow-states"] as const;
}

/** Lista já ordenada por `position` (garantido pelo backend) — mesma query
 * consumida pelo board, toolbar/formulário de issue e pelas configurações do
 * workspace, então raramente muda e nunca deveria "piscar" ao navegar entre
 * essas telas. */
export function useWorkflowStates(workspaceId: string) {
  return useQuery({
    queryKey: workflowStatesKey(workspaceId),
    queryFn: () => api.listWorkflowStates(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 30_000,
  });
}

function useInvalidateWorkflowStates(workspaceId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: workflowStatesKey(workspaceId) });
    // Um status pode mudar de categoria/nome/posição ou ser reatribuído/removido —
    // qualquer uma dessas invalida o que a lista de issues mostra (ícone/nome/coluna).
    queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "issues"] });
  };
}

export function useCreateWorkflowState(workspaceId: string) {
  const invalidate = useInvalidateWorkflowStates(workspaceId);
  return useMutation({
    mutationFn: (input: WorkflowStateCreateInput) => api.createWorkflowState(workspaceId, input),
    onSuccess: () => {
      invalidate();
      toast.success("Status criado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateWorkflowState(workspaceId: string, stateId: string) {
  const invalidate = useInvalidateWorkflowStates(workspaceId);
  return useMutation({
    mutationFn: (input: WorkflowStateUpdateInput) =>
      api.updateWorkflowState(workspaceId, stateId, input),
    onSuccess: () => {
      invalidate();
      toast.success("Status atualizado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteWorkflowState(workspaceId: string) {
  const invalidate = useInvalidateWorkflowStates(workspaceId);
  return useMutation({
    mutationFn: ({ stateId, reassignToId }: { stateId: string; reassignToId?: string }) =>
      api.deleteWorkflowState(workspaceId, stateId, reassignToId),
    onSuccess: () => {
      invalidate();
      toast.success("Status excluído.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useReorderWorkflowStates(workspaceId: string) {
  const invalidate = useInvalidateWorkflowStates(workspaceId);
  return useMutation({
    mutationFn: (orderedIds: string[]) => api.reorderWorkflowStates(workspaceId, orderedIds),
    onSuccess: () => invalidate(),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
