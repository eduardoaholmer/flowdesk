import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { DUE_DATE_MAX, DUE_DATE_MIN } from "@/shared/lib/constants";
import { isTypingTarget } from "@/shared/lib/dom";
import { useUiStore } from "@/shared/stores/uiStore";

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
  due_date: z
    .string()
    .optional()
    .refine((value) => !value || (value >= DUE_DATE_MIN && value <= DUE_DATE_MAX), {
      message: "Data de vencimento inválida.",
    }),
});

/**
 * Montado uma única vez em `AppLayout` (não por página) — controlado por
 * `uiStore.isCreateIssueOpen`, aberto pelo botão "Nova issue" da Sidebar, pelo
 * comando de mesmo nome na paleta, pelo atalho global `C`, ou pelos gatilhos
 * locais em `IssuesListPage`/`IssuesEmptyState` (todos só chamam
 * `setCreateIssueOpen(true)`, nenhum tem seu próprio estado/dialog).
 */
export function CreateIssueDialog({ workspaceId }: { workspaceId: string }) {
  const open = useUiStore((state) => state.isCreateIssueOpen);
  const setOpen = useUiStore((state) => state.setCreateIssueOpen);
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

  // Atalho global "C" (sem modificador) — mesmo gesto do handoff (`Sidebar.dc.html`/
  // `CommandPalette.dc.html`, "Nova issue · C"). Ignora quando o foco está num campo
  // de digitação (inclui o próprio input da paleta) para não interceptar a letra "c"
  // sendo digitada em um título/busca.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (open || event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key.toLowerCase() !== "c") return;
      if (isTypingTarget(event.target)) return;
      event.preventDefault();
      setOpen(true);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, setOpen]);

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
