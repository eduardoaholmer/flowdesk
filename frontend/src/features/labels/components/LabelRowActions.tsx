import { Pencil, Trash2 } from "lucide-react";

import { ConfirmActionDialog } from "@/shared/components/ConfirmActionDialog";
import { Button } from "@/shared/components/ui/button";

import { useDeleteLabel } from "../hooks";
import type { Label } from "../types";
import { EditLabelDialog } from "./EditLabelDialog";

export function LabelRowActions({ workspaceId, label }: { workspaceId: string; label: Label }) {
  const deleteLabel = useDeleteLabel(workspaceId);

  return (
    <div className="flex items-center gap-1">
      <EditLabelDialog
        workspaceId={workspaceId}
        label={label}
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Editar label">
            <Pencil />
          </Button>
        }
      />
      <ConfirmActionDialog
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Excluir label">
            <Trash2 />
          </Button>
        }
        title="Excluir label?"
        description={`"${label.name}" será removida do workspace e de todas as issues onde está aplicada.`}
        confirmLabel="Excluir"
        destructive
        isPending={deleteLabel.isPending}
        onConfirm={() => deleteLabel.mutate(label.id)}
      />
    </div>
  );
}
