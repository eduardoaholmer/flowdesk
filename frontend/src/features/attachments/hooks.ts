import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";
import type { Attachment } from "./types";

function attachmentsListKey(workspaceId: string, issueId: string) {
  return ["workspaces", workspaceId, "issues", "attachments", issueId] as const;
}

function issueActivityKey(workspaceId: string, issueId: string) {
  return ["workspaces", workspaceId, "issues", "activity", issueId] as const;
}

export function useAttachments(workspaceId: string, issueId: string) {
  return useQuery({
    queryKey: attachmentsListKey(workspaceId, issueId),
    queryFn: () => api.listAttachments(workspaceId, issueId),
    enabled: Boolean(workspaceId && issueId),
  });
}

function useInvalidateAttachments(workspaceId: string, issueId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: attachmentsListKey(workspaceId, issueId) });
    queryClient.invalidateQueries({ queryKey: issueActivityKey(workspaceId, issueId) });
  };
}

export function useUploadAttachment(workspaceId: string, issueId: string) {
  const invalidate = useInvalidateAttachments(workspaceId, issueId);
  return useMutation({
    mutationFn: (file: File) => api.uploadAttachment(workspaceId, issueId, file),
    onSuccess: () => invalidate(),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useDeleteAttachment(workspaceId: string, issueId: string) {
  const invalidate = useInvalidateAttachments(workspaceId, issueId);
  return useMutation({
    mutationFn: (attachmentId: string) => api.deleteAttachment(workspaceId, attachmentId),
    onSuccess: () => {
      invalidate();
      toast.success("Anexo excluído.");
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

/**
 * O access token só existe em memória (nunca em cookie/localStorage,
 * CLAUDE.md §11), então um `<a href>` puro para a rota de download não
 * carregaria o header `Authorization` — o arquivo precisa passar pelo
 * `httpClient` como blob antes de virar um link de download client-side.
 */
export function useDownloadAttachment(workspaceId: string) {
  return useMutation({
    mutationFn: async (attachment: Attachment) => {
      const blob = await api.downloadAttachment(workspaceId, attachment.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = attachment.file_name;
      link.click();
      URL.revokeObjectURL(url);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
