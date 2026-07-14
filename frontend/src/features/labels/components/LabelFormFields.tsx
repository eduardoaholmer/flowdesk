import type { FieldErrors, UseFormRegister } from "react-hook-form";

import { Input } from "@/shared/components/ui/input";
import { Label as FieldLabel } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";

export interface LabelFormValues {
  name: string;
  color: string;
  description?: string;
}

export function LabelFormFields({
  register,
  errors,
  idPrefix,
}: {
  register: UseFormRegister<LabelFormValues>;
  errors: FieldErrors<LabelFormValues>;
  idPrefix: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={`${idPrefix}-name`}>Nome</FieldLabel>
        <Input id={`${idPrefix}-name`} placeholder="bug" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={`${idPrefix}-color`}>Cor</FieldLabel>
        <Input id={`${idPrefix}-color`} placeholder="#4F46E5" {...register("color")} />
        {errors.color && <p className="text-xs text-destructive">{errors.color.message}</p>}
      </div>
      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={`${idPrefix}-description`}>Descrição</FieldLabel>
        <Textarea
          id={`${idPrefix}-description`}
          placeholder="Quando usar esta label?"
          {...register("description")}
        />
        {errors.description && (
          <p className="text-xs text-destructive">{errors.description.message}</p>
        )}
      </div>
    </div>
  );
}
