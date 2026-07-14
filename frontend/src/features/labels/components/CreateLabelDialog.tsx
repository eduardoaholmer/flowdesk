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

import { useCreateLabel } from "../hooks";
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

export function CreateLabelDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LabelFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { color: "#4F46E5" },
  });
  const createLabel = useCreateLabel(workspaceId);

  async function onSubmit(values: LabelFormValues) {
    await createLabel.mutateAsync({
      name: values.name,
      color: values.color,
      description: values.description || undefined,
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
        <Button>Nova label</Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Nova label</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <LabelFormFields register={register} errors={errors} idPrefix="create-label" />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createLabel.isPending}>
              {createLabel.isPending ? "Criando…" : "Criar label"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
