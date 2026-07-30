import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";

import { useUpdateWorkflowState } from "../hooks";
import type { WorkflowState } from "../types";
import { WorkflowStateFormFields, type WorkflowStateFormValues } from "./WorkflowStateFormFields";

const schema = z.object({
  name: z.string().min(1, "O nome não pode ser vazio.").max(50),
  category: z.enum(["BACKLOG", "UNSTARTED", "STARTED", "COMPLETED", "CANCELED"]),
  is_default: z.boolean(),
});

function toFormValues(state: WorkflowState): WorkflowStateFormValues {
  return { name: state.name, category: state.category, is_default: state.is_default };
}

export function EditWorkflowStateDialog({
  workspaceId,
  workflowState,
  trigger,
}: {
  workspaceId: string;
  workflowState: WorkflowState;
  trigger: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<WorkflowStateFormValues>({
    resolver: zodResolver(schema),
    defaultValues: toFormValues(workflowState),
  });
  const updateWorkflowState = useUpdateWorkflowState(workspaceId, workflowState.id);

  useEffect(() => {
    if (open) reset(toFormValues(workflowState));
  }, [open, workflowState, reset]);

  async function onSubmit(values: WorkflowStateFormValues) {
    await updateWorkflowState.mutateAsync(values);
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar status</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <WorkflowStateFormFields
              register={register}
              control={control}
              errors={errors}
              idPrefix="edit-workflow-state"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={updateWorkflowState.isPending}>
              {updateWorkflowState.isPending ? "Salvando…" : "Salvar alterações"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
