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

import { useUpdateLabel } from "../hooks";
import type { Label } from "../types";
import { LabelFormFields, type LabelFormValues } from "./LabelFormFields";

const schema = z.object({
  name: z.string().min(1, "O nome não pode ser vazio.").max(50),
  color: z
    .string()
    .regex(
      /^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/,
      "Use um código hexadecimal válido (ex.: #4F46E5).",
    ),
  description: z.string().max(280).optional(),
});

export function EditLabelDialog({
  workspaceId,
  label,
  trigger,
}: {
  workspaceId: string;
  label: Label;
  trigger: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LabelFormValues>({
    resolver: zodResolver(schema),
    values: {
      name: label.name,
      color: label.color,
      description: label.description ?? "",
    },
  });
  const updateLabel = useUpdateLabel(workspaceId, label.id);

  useEffect(() => {
    if (!open) reset();
  }, [open, reset]);

  async function onSubmit(values: LabelFormValues) {
    await updateLabel.mutateAsync({
      name: values.name,
      color: values.color,
      description: values.description || undefined,
    });
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar label</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <LabelFormFields register={register} errors={errors} idPrefix="edit-label" />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={updateLabel.isPending}>
              {updateLabel.isPending ? "Salvando…" : "Salvar alterações"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
