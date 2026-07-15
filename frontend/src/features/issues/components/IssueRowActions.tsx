import { Pencil, Trash2 } from "lucide-react";

import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Button } from "@/shared/components/ui/button";

import { useDeleteIssue } from "../hooks";
import type { Issue } from "../types";
import { EditIssueDialog } from "./EditIssueDialog";

export function IssueRowActions({
  workspaceId,
  issue,
  onDeleted,
}: {
  workspaceId: string;
  issue: Issue;
  onDeleted?: () => void;
}) {
  const deleteIssue = useDeleteIssue(workspaceId);

  return (
    <div className="flex items-center gap-1">
      <EditIssueDialog
        workspaceId={workspaceId}
        issue={issue}
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Editar issue">
            <Pencil />
          </Button>
        }
      />
      <ConfirmActionDialog
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Excluir issue">
            <Trash2 />
          </Button>
        }
        title="Excluir issue?"
        description={`"${issue.identifier} — ${issue.title}" será excluída.`}
        confirmLabel="Excluir"
        destructive
        isPending={deleteIssue.isPending}
        onConfirm={() =>
          deleteIssue.mutate(issue.id, {
            onSuccess: onDeleted,
          })
        }
      />
    </div>
  );
}
