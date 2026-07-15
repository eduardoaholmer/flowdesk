import { useState } from "react";
import { Pencil, Trash2 } from "lucide-react";

import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Button } from "@/shared/components/ui/button";
import { Textarea } from "@/shared/components/ui/textarea";
import { formatDateTime } from "@/shared/lib/date";
import { getInitials } from "@/shared/lib/string";

import { useDeleteComment, useUpdateComment } from "../hooks";
import type { Comment } from "../types";

export function CommentItem({
  workspaceId,
  issueId,
  comment,
  authorName,
  isOwnComment,
}: {
  workspaceId: string;
  issueId: string;
  comment: Comment;
  authorName: string;
  isOwnComment: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(comment.body);
  const updateComment = useUpdateComment(workspaceId, issueId, comment.id);
  const deleteComment = useDeleteComment(workspaceId, issueId);

  function handleSave() {
    const trimmed = draft.trim();
    if (!trimmed) return;
    updateComment.mutate({ body: trimmed }, { onSuccess: () => setIsEditing(false) });
  }

  return (
    <div className="flex gap-3">
      <Avatar size="sm">
        <AvatarFallback>{getInitials(authorName)}</AvatarFallback>
      </Avatar>
      <div className="flex-1">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-medium">{authorName}</span>
            <span className="text-xs text-muted-foreground">
              {formatDateTime(comment.created_at)}
            </span>
            {comment.updated_at !== comment.created_at && (
              <span className="text-xs text-muted-foreground">(editado)</span>
            )}
          </div>
          {isOwnComment && !isEditing && (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Editar comentário"
                onClick={() => {
                  setDraft(comment.body);
                  setIsEditing(true);
                }}
              >
                <Pencil />
              </Button>
              <ConfirmActionDialog
                trigger={
                  <Button variant="ghost" size="icon-sm" aria-label="Excluir comentário">
                    <Trash2 />
                  </Button>
                }
                title="Excluir comentário?"
                description="Esta ação não pode ser desfeita."
                confirmLabel="Excluir"
                destructive
                isPending={deleteComment.isPending}
                onConfirm={() => deleteComment.mutate(comment.id)}
              />
            </div>
          )}
        </div>

        {isEditing ? (
          <div className="mt-2 flex flex-col gap-2">
            <Textarea value={draft} onChange={(event) => setDraft(event.target.value)} rows={3} />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                Cancelar
              </Button>
              <Button
                size="sm"
                disabled={!draft.trim() || updateComment.isPending}
                onClick={handleSave}
              >
                {updateComment.isPending ? "Salvando…" : "Salvar"}
              </Button>
            </div>
          </div>
        ) : (
          <p className="mt-1 text-sm whitespace-pre-wrap">{comment.body}</p>
        )}
      </div>
    </div>
  );
}
