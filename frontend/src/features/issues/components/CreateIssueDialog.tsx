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

import { useCreateIssue } from "../hooks";
import { IssueFormFields, type IssueFormValues } from "./IssueFormFields";

const schema = z.object({
  title: z.string().min(1, "O título é obrigatório.").max(255),
  description: z.string().optional(),
  project_id: z.string().optional(),
  status: z.enum(["BACKLOG", "TODO", "IN_PROGRESS", "IN_REVIEW", "DONE", "CANCELED"]),
  priority: z.enum(["NO_PRIORITY", "LOW", "MEDIUM", "HIGH", "URGENT"]),
  assignee_id: z.string().optional(),
  estimate: z.string().optional(),
  due_date: z.string().optional(),
});

export function CreateIssueDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<IssueFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { status: "BACKLOG", priority: "NO_PRIORITY" },
  });
  const createIssue = useCreateIssue(workspaceId);

  async function onSubmit(values: IssueFormValues) {
    await createIssue.mutateAsync({
      title: values.title,
      description: values.description || undefined,
      project_id: values.project_id || undefined,
      status: values.status,
      priority: values.priority,
      assignee_id: values.assignee_id || undefined,
      estimate: values.estimate ? Number(values.estimate) : undefined,
      due_date: values.due_date || undefined,
    });
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
        <Button>Nova issue</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Nova issue</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <IssueFormFields
              workspaceId={workspaceId}
              register={register}
              control={control}
              errors={errors}
              idPrefix="create-issue"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createIssue.isPending}>
              {createIssue.isPending ? "Criando…" : "Criar issue"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
