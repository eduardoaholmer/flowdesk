import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { Attachment } from "./types";

export async function listAttachments(workspaceId: string, issueId: string): Promise<Attachment[]> {
  const { data } = await httpClient.get<DataEnvelope<Attachment[]>>(
    `/workspaces/${workspaceId}/issues/${issueId}/attachments`,
  );
  return data.data;
}

export async function uploadAttachment(
  workspaceId: string,
  issueId: string,
  file: File,
): Promise<Attachment> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await httpClient.post<DataEnvelope<Attachment>>(
    `/workspaces/${workspaceId}/issues/${issueId}/attachments`,
    formData,
  );
  return data.data;
}

export async function deleteAttachment(workspaceId: string, attachmentId: string): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/attachments/${attachmentId}`);
}

export async function downloadAttachment(workspaceId: string, attachmentId: string): Promise<Blob> {
  const { data } = await httpClient.get<Blob>(
    `/workspaces/${workspaceId}/attachments/${attachmentId}`,
    { responseType: "blob" },
  );
  return data;
}
