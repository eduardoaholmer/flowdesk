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

import { useUpdateProject } from "../hooks";
import type { Project } from "../types";
import { ProjectFormFields, type ProjectFormValues } from "./ProjectFormFields";

const schema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres.").max(100),
  description: z.string().optional(),
  icon: z.string().max(64).optional(),
  color: z
    .string()
    .optional()
    .refine((value) => !value || /^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/.test(value), {
      message: "Use um código hexadecimal válido (ex.: #4F46E5).",
    }),
});

export function EditProjectDialog({
  workspaceId,
  project,
  trigger,
}: {
  workspaceId: string;
  project: Project;
  trigger: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(schema),
    values: {
      name: project.name,
      description: project.description ?? "",
      icon: project.icon ?? "",
      color: project.color ?? "",
    },
  });
  const updateProject = useUpdateProject(workspaceId, project.id);

  useEffect(() => {
    if (!open) reset();
  }, [open, reset]);

  async function onSubmit(values: ProjectFormValues) {
    await updateProject.mutateAsync({
      name: values.name,
      description: values.description || undefined,
      icon: values.icon || undefined,
      color: values.color || undefined,
    });
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Editar projeto</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <ProjectFormFields
              register={register}
              control={control}
              errors={errors}
              idPrefix="edit-project"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={updateProject.isPending}>
              {updateProject.isPending ? "Salvando…" : "Salvar alterações"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
