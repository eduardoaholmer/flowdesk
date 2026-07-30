import { useState } from "react";

import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Button } from "@/shared/components/ui/button";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";

import { useDeleteWorkflowState } from "../hooks";
import type { WorkflowState } from "../types";

/** Chamador garante `allStates.length > 1` (excluir o último status é bloqueado
 * antes de chegar aqui — ver `WorkflowStateRowActions`, que desabilita o botão). */
export function DeleteWorkflowStateDialog({
  workspaceId,
  workflowState,
  allStates,
  trigger,
}: {
  workspaceId: string;
  workflowState: WorkflowState;
  allStates: WorkflowState[];
  trigger: React.ReactNode;
}) {
  const deleteWorkflowState = useDeleteWorkflowState(workspaceId);
  const otherStates = allStates.filter((state) => state.id !== workflowState.id);

  if (workflowState.issue_count === 0) {
    return (
      <ConfirmActionDialog
        trigger={trigger}
        title="Excluir status?"
        description={`"${workflowState.name}" será removido do workspace.`}
        confirmLabel="Excluir"
        destructive
        isPending={deleteWorkflowState.isPending}
        onConfirm={() => deleteWorkflowState.mutate({ stateId: workflowState.id })}
      />
    );
  }

  return (
    <ReassignAndDeleteDialog
      workflowState={workflowState}
      otherStates={otherStates}
      trigger={trigger}
      isPending={deleteWorkflowState.isPending}
      onConfirm={(reassignToId) =>
        deleteWorkflowState.mutate({ stateId: workflowState.id, reassignToId })
      }
    />
  );
}

function ReassignAndDeleteDialog({
  workflowState,
  otherStates,
  trigger,
  isPending,
  onConfirm,
}: {
  workflowState: WorkflowState;
  otherStates: WorkflowState[];
  trigger: React.ReactNode;
  isPending: boolean;
  onConfirm: (reassignToId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [reassignToId, setReassignToId] = useState<string>(otherStates[0]?.id ?? "");

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Excluir "{workflowState.name}"?</DialogTitle>
          <DialogDescription>
            {workflowState.issue_count}{" "}
            {workflowState.issue_count === 1 ? "issue está" : "issues estão"} com este status.
            Escolha para qual status reatribuí-las antes de excluir.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-1.5 py-2">
          <Label>Reatribuir para</Label>
          <Select value={reassignToId} onValueChange={setReassignToId}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {otherStates.map((state) => (
                <SelectItem key={state.id} value={state.id}>
                  {state.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            disabled={isPending || !reassignToId}
            onClick={() => {
              onConfirm(reassignToId);
              setOpen(false);
            }}
          >
            {isPending ? "Excluindo…" : "Reatribuir e excluir"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
