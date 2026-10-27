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

import { useCreateProject } from "../hooks";
import { ProjectFormFields, type ProjectFormValues } from "./ProjectFormFields";

const schema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres.").max(100),
  key: z
    .string()
    .optional()
    .refine((value) => !value || /^[A-Za-z]{2,4}$/.test(value), {
      message: "A key deve ter de 2 a 4 letras (ex.: ONB).",
    }),
  description: z.string().optional(),
  icon: z.string().max(64).optional(),
  color: z
    .string()
    .optional()
    .refine((value) => !value || /^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/.test(value), {
      message: "Use um código hexadecimal válido (ex.: #4F46E5).",
    }),
  lead_id: z.string().optional(),
  target_date: z.string().optional(),
});

export function CreateProjectDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormValues>({ resolver: zodResolver(schema) });
  const createProject = useCreateProject(workspaceId);

  async function onSubmit(values: ProjectFormValues) {
    await createProject.mutateAsync({
      name: values.name,
      key: values.key ? values.key.toUpperCase() : undefined,
      description: values.description || undefined,
      icon: values.icon || undefined,
      color: values.color || undefined,
      lead_id: values.lead_id || undefined,
      target_date: values.target_date || undefined,
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
        <Button>Novo projeto</Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Novo projeto</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <ProjectFormFields
              workspaceId={workspaceId}
              register={register}
              control={control}
              errors={errors}
              idPrefix="create-project"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? "Criando…" : "Criar projeto"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
