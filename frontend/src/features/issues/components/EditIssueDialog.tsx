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

import { useUpdateIssue } from "../hooks";
import type { Issue } from "../types";
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

export function EditIssueDialog({
  workspaceId,
  issue,
  trigger,
}: {
  workspaceId: string;
  issue: Issue;
  trigger: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<IssueFormValues>({
    resolver: zodResolver(schema),
    values: {
      title: issue.title,
      description: issue.description ?? "",
      project_id: issue.project_id ?? undefined,
      status: issue.status,
      priority: issue.priority,
      assignee_id: issue.assignee_id ?? undefined,
      estimate: issue.estimate !== null ? String(issue.estimate) : "",
      due_date: issue.due_date ?? "",
    },
  });
  const updateIssue = useUpdateIssue(workspaceId, issue.id);

  useEffect(() => {
    if (!open) reset();
  }, [open, reset]);

  async function onSubmit(values: IssueFormValues) {
    await updateIssue.mutateAsync({
      title: values.title,
      description: values.description || undefined,
      project_id: values.project_id || undefined,
      status: values.status,
      priority: values.priority,
      assignee_id: values.assignee_id || undefined,
      estimate: values.estimate ? Number(values.estimate) : undefined,
      due_date: values.due_date || undefined,
    });
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar issue</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <IssueFormFields
              workspaceId={workspaceId}
              register={register}
              control={control}
              errors={errors}
              idPrefix="edit-issue"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={updateIssue.isPending}>
              {updateIssue.isPending ? "Salvando…" : "Salvar alterações"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
