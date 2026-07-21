import type { Control, FieldErrors, UseFormRegister } from "react-hook-form";
import { Controller } from "react-hook-form";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { ColorSwatchPicker } from "@/shared/components/pickers/ColorSwatchPicker";
import { EmojiIconPicker } from "@/shared/components/pickers/EmojiIconPicker";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Textarea } from "@/shared/components/ui/textarea";

export interface ProjectFormValues {
  name: string;
  key?: string;
  description?: string;
  icon?: string;
  color?: string;
  lead_id?: string;
  target_date?: string;
}

const NONE = "__none__";

export function ProjectFormFields({
  workspaceId,
  register,
  control,
  errors,
  idPrefix,
}: {
  workspaceId: string;
  register: UseFormRegister<ProjectFormValues>;
  control: Control<ProjectFormValues>;
  errors: FieldErrors<ProjectFormValues>;
  idPrefix: string;
}) {
  const { data: members } = useWorkspaceMembers(workspaceId);

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-[1fr_auto] gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-name`}>Nome</Label>
          <Input id={`${idPrefix}-name`} placeholder="Roadmap Q3" {...register("name")} />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-key`}>Key</Label>
          <Input
            id={`${idPrefix}-key`}
            placeholder="Auto"
            className="w-24 uppercase"
            {...register("key")}
          />
          {errors.key && <p className="text-xs text-destructive">{errors.key.message}</p>}
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-description`}>Descrição</Label>
        <Textarea
          id={`${idPrefix}-description`}
          placeholder="Sobre o que é este projeto?"
          {...register("description")}
        />
        {errors.description && (
          <p className="text-xs text-destructive">{errors.description.message}</p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label>Líder</Label>
          <Controller
            control={control}
            name="lead_id"
            render={({ field }) => (
              <Select
                value={field.value ?? NONE}
                onValueChange={(value) => field.onChange(value === NONE ? undefined : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sem líder" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE}>Sem líder</SelectItem>
                  {members?.map((member) => (
                    <SelectItem key={member.user.id} value={member.user.id}>
                      {member.user.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-target-date`}>Entrega prevista</Label>
          <Input id={`${idPrefix}-target-date`} type="date" {...register("target_date")} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-icon`}>Ícone</Label>
          <Controller
            control={control}
            name="icon"
            render={({ field }) => (
              <EmojiIconPicker
                id={`${idPrefix}-icon`}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          {errors.icon && <p className="text-xs text-destructive">{errors.icon.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-color`}>Cor</Label>
          <Controller
            control={control}
            name="color"
            render={({ field }) => (
              <ColorSwatchPicker
                id={`${idPrefix}-color`}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          {errors.color && <p className="text-xs text-destructive">{errors.color.message}</p>}
        </div>
      </div>
    </div>
  );
}
