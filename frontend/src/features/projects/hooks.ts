import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { ProjectCreateInput, ProjectListParams, ProjectUpdateInput } from "./types";

function projectsListKey(workspaceId: string, params: ProjectListParams) {
  return ["workspaces", workspaceId, "projects", params] as const;
}

function projectKey(workspaceId: string, projectId: string) {
  return ["workspaces", workspaceId, "projects", "detail", projectId] as const;
}

export function useProjects(workspaceId: string, params: ProjectListParams) {
  return useQuery({
    queryKey: projectsListKey(workspaceId, params),
    queryFn: () => api.listProjects(workspaceId, params),
    enabled: Boolean(workspaceId),
    placeholderData: keepPreviousData,
  });
}

export function useProject(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: projectKey(workspaceId, projectId),
    queryFn: () => api.getProject(workspaceId, projectId),
    enabled: Boolean(workspaceId && projectId),
  });
}

function useInvalidateProjects(workspaceId: string) {
  const queryClient = useQueryClient();
  return (projectId?: string) => {
    queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "projects"] });
    if (projectId) {
      queryClient.invalidateQueries({ queryKey: projectKey(workspaceId, projectId) });
    }
  };
}

export function useCreateProject(workspaceId: string) {
  const invalidate = useInvalidateProjects(workspaceId);
  return useMutation({
    mutationFn: (input: ProjectCreateInput) => api.createProject(workspaceId, input),
    onSuccess: () => {
      invalidate();
      toast.success("Projeto criado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useUpdateProject(workspaceId: string, projectId: string) {
  const invalidate = useInvalidateProjects(workspaceId);
  return useMutation({
    mutationFn: (input: ProjectUpdateInput) => api.updateProject(workspaceId, projectId, input),
    onSuccess: () => {
      invalidate(projectId);
      toast.success("Projeto atualizado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useArchiveProject(workspaceId: string) {
  const invalidate = useInvalidateProjects(workspaceId);
  return useMutation({
    mutationFn: (projectId: string) => api.archiveProject(workspaceId, projectId),
    onSuccess: (_data, projectId) => {
      invalidate(projectId);
      toast.success("Projeto arquivado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useRestoreProject(workspaceId: string) {
  const invalidate = useInvalidateProjects(workspaceId);
  return useMutation({
    mutationFn: (projectId: string) => api.restoreProject(workspaceId, projectId),
    onSuccess: (_data, projectId) => {
      invalidate(projectId);
      toast.success("Projeto restaurado.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteProject(workspaceId: string) {
  const invalidate = useInvalidateProjects(workspaceId);
  return useMutation({
    mutationFn: (projectId: string) => api.deleteProject(workspaceId, projectId),
    onSuccess: () => {
      invalidate();
      toast.success("Projeto excluído.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
