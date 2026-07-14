import { useRef } from "react";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";

import { useAttachments, useUploadAttachment } from "../hooks";
import { AttachmentItem } from "./AttachmentItem";

export function AttachmentList({ workspaceId, issueId }: { workspaceId: string; issueId: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: attachments, isLoading } = useAttachments(workspaceId, issueId);
  const { data: members } = useWorkspaceMembers(workspaceId);
  const { data: currentUser } = useCurrentUser();
  const uploadAttachment = useUploadAttachment(workspaceId, issueId);

  function uploaderName(uploaderId: string): string {
    if (uploaderId === currentUser?.id) return "Você";
    return members?.find((member) => member.user.id === uploaderId)?.user.name ?? "Alguém";
  }

  function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    uploadAttachment.mutate(file);
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <input ref={inputRef} type="file" className="hidden" onChange={handleFileSelected} />
        <Button
          variant="outline"
          size="sm"
          disabled={uploadAttachment.isPending}
          onClick={() => inputRef.current?.click()}
        >
          {uploadAttachment.isPending ? "Enviando…" : "Anexar arquivo"}
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-12 w-full" />
      ) : !attachments || attachments.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhum anexo ainda.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {attachments.map((attachment) => (
            <AttachmentItem
              key={attachment.id}
              workspaceId={workspaceId}
              issueId={issueId}
              attachment={attachment}
              uploaderName={uploaderName(attachment.uploader_id)}
              isOwnAttachment={attachment.uploader_id === currentUser?.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
