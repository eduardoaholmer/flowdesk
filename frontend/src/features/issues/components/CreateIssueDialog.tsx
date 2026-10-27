import { zodResolver } from "@hookform/resolvers/zod";
import { Tag } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { useLabels } from "@/features/labels/hooks";
import { LabelBadge } from "@/features/labels/components/LabelBadge";
import { LabelCombobox } from "@/features/labels/components/LabelCombobox";
import { useWorkflowStates } from "@/features/workflow-states/hooks";
import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Label } from "@/shared/components/ui/label";
import { DUE_DATE_MAX, DUE_DATE_MIN } from "@/shared/lib/constants";
import { isTypingTarget } from "@/shared/lib/dom";
import { useUiStore } from "@/shared/stores/uiStore";

import { useCreateIssue, useIssue } from "../hooks";
import { IssueFormFields, type IssueFormValues } from "./IssueFormFields";

const schema = z.object({
  title: z.string().min(1, "O título é obrigatório.").max(255),
  description: z.string().optional(),
  project_id: z.string().optional(),
  status_id: z.string().min(1, "Selecione um status."),
  priority: z.enum(["NO_PRIORITY", "LOW", "MEDIUM", "HIGH", "URGENT"]),
  assignee_id: z.string().optional(),
  estimate: z.string().optional(),
  due_date: z
    .string()
    .optional()
    .refine((value) => !value || (value >= DUE_DATE_MIN && value <= DUE_DATE_MAX), {
      message: "Data de vencimento inválida.",
    }),
  label_ids: z.array(z.string()).optional(),
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
  const parentId = useUiStore((state) => state.createIssueParentId);
  const setCreateIssueParentId = useUiStore((state) => state.setCreateIssueParentId);
  const { data: parentIssue } = useIssue(workspaceId, parentId ?? "");
  const {
    register,
    handleSubmit,
    control,
    reset,
    setValue,
    formState: { errors },
  } = useForm<IssueFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { status_id: "", priority: "NO_PRIORITY", label_ids: [] },
  });
  const createIssue = useCreateIssue(workspaceId);
  const { data: workflowStates } = useWorkflowStates(workspaceId);

  // Preseleciona o status padrão do workspace assim que a lista carrega — o
  // backend também assumiria esse default se o campo fosse omitido, mas
  // manter um valor visível no select reproduz o comportamento anterior
  // (enum fixo com default "BACKLOG" hardcoded).
  useEffect(() => {
    if (!open || !workflowStates) return;
    const defaultState = workflowStates.find((state) => state.is_default) ?? workflowStates.at(0);
    if (!defaultState) return;
    setValue("status_id", defaultState.id);
  }, [open, workflowStates, setValue]);

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
      parent_id: parentId ?? undefined,
      status_id: values.status_id,
      priority: values.priority,
      assignee_id: values.assignee_id || undefined,
      estimate: values.estimate ? Number(values.estimate) : undefined,
      due_date: values.due_date || undefined,
      label_ids: values.label_ids?.length ? values.label_ids : undefined,
    });
    reset();
    setOpen(false);
    setCreateIssueParentId(null);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) {
          reset();
          setCreateIssueParentId(null);
        }
      }}
    >
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>
              {parentIssue ? `Nova sub-issue de ${parentIssue.identifier}` : "Nova issue"}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <IssueFormFields
              workspaceId={workspaceId}
              register={register}
              control={control}
              errors={errors}
              idPrefix="create-issue"
            />
            <div className="mt-4 flex flex-col gap-1.5">
              <Label>Labels</Label>
              <Controller
                control={control}
                name="label_ids"
                render={({ field }) => (
                  <IssueLabelsField
                    workspaceId={workspaceId}
                    value={field.value ?? []}
                    onChange={field.onChange}
                  />
                )}
              />
            </div>
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

function IssueLabelsField({
  workspaceId,
  value,
  onChange,
}: {
  workspaceId: string;
  value: string[];
  onChange: (labelIds: string[]) => void;
}) {
  const { data: labels = [] } = useLabels(workspaceId);
  const selectedIds = new Set(value);
  const selectedLabels = labels.filter((label) => selectedIds.has(label.id));

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {selectedLabels.map((label) => (
        <LabelBadge key={label.id} label={label} />
      ))}
      <LabelCombobox
        workspaceId={workspaceId}
        selectedIds={selectedIds}
        onToggle={(label, selected) =>
          onChange(selected ? [...value, label.id] : value.filter((id) => id !== label.id))
        }
      >
        <Button type="button" variant="outline" size="sm">
          <Tag />
          {selectedLabels.length > 0 ? "Editar labels" : "Adicionar labels"}
        </Button>
      </LabelCombobox>
    </div>
  );
}
