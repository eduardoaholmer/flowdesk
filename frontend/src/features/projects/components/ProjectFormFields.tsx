import type { FieldErrors, UseFormRegister } from "react-hook-form";

import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";

export interface ProjectFormValues {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
}

export function ProjectFormFields({
  register,
  errors,
  idPrefix,
}: {
  register: UseFormRegister<ProjectFormValues>;
  errors: FieldErrors<ProjectFormValues>;
  idPrefix: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-name`}>Nome</Label>
        <Input id={`${idPrefix}-name`} placeholder="Roadmap Q3" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
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
          <Label htmlFor={`${idPrefix}-icon`}>Ícone</Label>
          <Input id={`${idPrefix}-icon`} placeholder="🚀" {...register("icon")} />
          {errors.icon && <p className="text-xs text-destructive">{errors.icon.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-color`}>Cor</Label>
          <div className="flex items-center gap-2">
            <Input
              id={`${idPrefix}-color`}
              placeholder="#4F46E5"
              {...register("color")}
              className="flex-1"
            />
          </div>
          {errors.color && <p className="text-xs text-destructive">{errors.color.message}</p>}
        </div>
      </div>
    </div>
  );
}
