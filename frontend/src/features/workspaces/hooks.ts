import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { InvitationCreateInput, WorkspaceMember, WorkspaceUpdateInput } from "./types";

function workspaceKey(workspaceId: string) {
  return ["workspaces", workspaceId] as const;
}

function membersKey(workspaceId: string) {
  return ["workspaces", workspaceId, "members"] as const;
}

function invitationsKey(workspaceId: string) {
  return ["workspaces", workspaceId, "invitations"] as const;
}

/** Busca o recurso completo (inclui `description`, ausente de `WorkspaceMembershipSummary`
 * em `useWorkspace()`/`useWorkspace.ts`, que só resolve id/nome/slug/role a partir do
 * perfil) — usado pela aba "Geral" das configurações do workspace. */
export function useWorkspaceDetail(workspaceId: string) {
  return useQuery({
    queryKey: workspaceKey(workspaceId),
    queryFn: () => api.getWorkspace(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 60_000,
  });
}

export function useWorkspaceMembers(workspaceId: string) {
  return useQuery({
    queryKey: membersKey(workspaceId),
    queryFn: () => api.listWorkspaceMembers(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 60_000,
  });
}

export function useInvitations(workspaceId: string) {
  return useQuery({
    queryKey: invitationsKey(workspaceId),
    queryFn: () => api.listInvitations(workspaceId),
    enabled: Boolean(workspaceId),
    staleTime: 30_000,
  });
}

export function useUpdateWorkspace(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: WorkspaceUpdateInput) => api.updateWorkspace(workspaceId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKey(workspaceId) });
      queryClient.invalidateQueries({ queryKey: ["users", "me"] });
      toast.success("Workspace atualizado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteWorkspace(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.deleteWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "me"] });
      toast.success("Workspace excluído.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateMemberRole(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: WorkspaceMember["role"] }) => {
      if (role === "OWNER") {
        throw new Error("Não é possível promover um membro a OWNER por esta ação.");
      }
      return api.updateMemberRole(workspaceId, memberId, role);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: membersKey(workspaceId) });
      toast.success("Papel do membro atualizado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useRemoveMember(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (memberId: string) => api.removeMember(workspaceId, memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: membersKey(workspaceId) });
      toast.success("Membro removido do workspace.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useLeaveWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workspaceId: string) => api.leaveWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "me"] });
      toast.success("Você saiu do workspace.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useCreateInvitation(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: InvitationCreateInput) => api.createInvitation(workspaceId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invitationsKey(workspaceId) });
      toast.success("Convite criado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useCancelInvitation(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (invitationId: string) => api.cancelInvitation(workspaceId, invitationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invitationsKey(workspaceId) });
      toast.success("Convite cancelado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (token: string) => api.acceptInvitation(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "me"] });
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
