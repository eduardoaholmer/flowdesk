import type { Control, FieldErrors, UseFormRegister } from "react-hook-form";
import { Controller } from "react-hook-form";

import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Switch } from "@/shared/components/ui/switch";

import { WORKFLOW_STATE_CATEGORY_LABELS, WORKFLOW_STATE_CATEGORY_ORDER } from "../constants";
import type { WorkflowStateCategory } from "../types";

export interface WorkflowStateFormValues {
  name: string;
  category: WorkflowStateCategory;
  is_default: boolean;
}

export function WorkflowStateFormFields({
  register,
  control,
  errors,
  idPrefix,
}: {
  register: UseFormRegister<WorkflowStateFormValues>;
  control: Control<WorkflowStateFormValues>;
  errors: FieldErrors<WorkflowStateFormValues>;
  idPrefix: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-name`}>Nome</Label>
        <Input id={`${idPrefix}-name`} placeholder="Em revisão" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label>Categoria</Label>
        <Controller
          control={control}
          name="category"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {WORKFLOW_STATE_CATEGORY_ORDER.map((category) => (
                  <SelectItem key={category} value={category}>
                    {WORKFLOW_STATE_CATEGORY_LABELS[category]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        <p className="text-xs text-muted-foreground">
          Define o que este status conta como (ex.: progresso do projeto) — independente do nome.
        </p>
      </div>

      <div className="flex items-center justify-between gap-4 rounded-lg border p-3">
        <div>
          <Label htmlFor={`${idPrefix}-is-default`}>Status padrão</Label>
          <p className="text-xs text-muted-foreground">
            Atribuído a issues novas quando nenhum status é informado.
          </p>
        </div>
        <Controller
          control={control}
          name="is_default"
          render={({ field }) => (
            <Switch
              id={`${idPrefix}-is-default`}
              checked={field.value}
              onCheckedChange={field.onChange}
            />
          )}
        />
      </div>
    </div>
  );
}
