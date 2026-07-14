import { Download, Paperclip, Trash2 } from "lucide-react";

import { ConfirmActionDialog } from "@/shared/components/ConfirmActionDialog";
import { Button } from "@/shared/components/ui/button";

import { useDeleteAttachment, useDownloadAttachment } from "../hooks";
import type { Attachment } from "../types";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentItem({
  workspaceId,
  issueId,
  attachment,
  uploaderName,
  isOwnAttachment,
}: {
  workspaceId: string;
  issueId: string;
  attachment: Attachment;
  uploaderName: string;
  isOwnAttachment: boolean;
}) {
  const downloadAttachment = useDownloadAttachment(workspaceId);
  const deleteAttachment = useDeleteAttachment(workspaceId, issueId);

  return (
    <div className="flex items-center gap-3 rounded-md border p-2 text-sm">
      <Paperclip className="size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{attachment.file_name}</p>
        <p className="text-xs text-muted-foreground">
          {formatFileSize(attachment.file_size)} · enviado por {uploaderName}
        </p>
      </div>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Baixar anexo"
        disabled={downloadAttachment.isPending}
        onClick={() => downloadAttachment.mutate(attachment)}
      >
        <Download />
      </Button>
      {isOwnAttachment && (
        <ConfirmActionDialog
          trigger={
            <Button variant="ghost" size="icon-sm" aria-label="Excluir anexo">
              <Trash2 />
            </Button>
          }
          title="Excluir anexo?"
          description={`"${attachment.file_name}" será excluído. Esta ação não pode ser desfeita.`}
          confirmLabel="Excluir"
          destructive
          isPending={deleteAttachment.isPending}
          onConfirm={() => deleteAttachment.mutate(attachment.id)}
        />
      )}
    </div>
  );
}
