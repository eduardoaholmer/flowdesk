import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
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

import { useCreateWorkflowState } from "../hooks";
import { WorkflowStateFormFields, type WorkflowStateFormValues } from "./WorkflowStateFormFields";

const schema = z.object({
  name: z.string().min(1, "O nome não pode ser vazio.").max(50),
  category: z.enum(["BACKLOG", "UNSTARTED", "STARTED", "COMPLETED", "CANCELED"]),
  is_default: z.boolean(),
});

export function CreateWorkflowStateDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<WorkflowStateFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { category: "UNSTARTED", is_default: false },
  });
  const createWorkflowState = useCreateWorkflowState(workspaceId);

  async function onSubmit(values: WorkflowStateFormValues) {
    await createWorkflowState.mutateAsync(values);
    reset();
    setOpen(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button>Novo status</Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Novo status</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <WorkflowStateFormFields
              register={register}
              control={control}
              errors={errors}
              idPrefix="create-workflow-state"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createWorkflowState.isPending}>
              {createWorkflowState.isPending ? "Criando…" : "Criar status"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
