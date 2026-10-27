import { ArrowDown, ArrowUp, Pencil, Trash2 } from "lucide-react";

import { Button } from "@/shared/components/ui/button";

import { useReorderWorkflowStates } from "../hooks";
import type { WorkflowState } from "../types";
import { DeleteWorkflowStateDialog } from "./DeleteWorkflowStateDialog";
import { EditWorkflowStateDialog } from "./EditWorkflowStateDialog";

export function WorkflowStateRowActions({
  workspaceId,
  workflowState,
  allStates,
  index,
}: {
  workspaceId: string;
  workflowState: WorkflowState;
  allStates: WorkflowState[];
  index: number;
}) {
  const reorder = useReorderWorkflowStates(workspaceId);

  function move(offset: number) {
    const next = [...allStates];
    const [moved] = next.splice(index, 1);
    if (!moved) return;
    next.splice(index + offset, 0, moved);
    reorder.mutate(next.map((state) => state.id));
  }

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Mover para cima"
        disabled={index === 0 || reorder.isPending}
        onClick={() => move(-1)}
      >
        <ArrowUp />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Mover para baixo"
        disabled={index === allStates.length - 1 || reorder.isPending}
        onClick={() => move(1)}
      >
        <ArrowDown />
      </Button>
      <EditWorkflowStateDialog
        workspaceId={workspaceId}
        workflowState={workflowState}
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Editar status">
            <Pencil />
          </Button>
        }
      />
      {allStates.length > 1 ? (
        <DeleteWorkflowStateDialog
          workspaceId={workspaceId}
          workflowState={workflowState}
          allStates={allStates}
          trigger={
            <Button variant="ghost" size="icon-sm" aria-label="Excluir status">
              <Trash2 />
            </Button>
          }
        />
      ) : (
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Excluir status"
          disabled
          title="O workspace precisa de ao menos um status."
        >
          <Trash2 />
        </Button>
      )}
    </div>
  );
}
