import type { Control, FieldErrors, UseFormRegister } from "react-hook-form";
import { Controller } from "react-hook-form";

import { ColorSwatchPicker } from "@/shared/components/pickers/ColorSwatchPicker";
import { EmojiIconPicker } from "@/shared/components/pickers/EmojiIconPicker";
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
  control,
  errors,
  idPrefix,
}: {
  register: UseFormRegister<ProjectFormValues>;
  control: Control<ProjectFormValues>;
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
