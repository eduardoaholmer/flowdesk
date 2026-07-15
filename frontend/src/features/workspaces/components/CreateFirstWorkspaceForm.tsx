import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { workspaceRoutes } from "@/shared/lib/routes";

import { createWorkspace } from "../api";

const schema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres."),
});

type Values = z.infer<typeof schema>;

export function CreateFirstWorkspaceForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) });

  async function onSubmit(values: Values) {
    setIsSubmitting(true);
    try {
      const workspace = await createWorkspace(values.name);
      await queryClient.invalidateQueries({ queryKey: ["users", "me"] });
      navigate(workspaceRoutes.projects(workspace.slug), { replace: true });
    } catch {
      toast.error("Não foi possível criar o workspace.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="workspace-name">Nome do workspace</Label>
        <Input id="workspace-name" placeholder="Acme Inc" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Criando…" : "Criar workspace"}
      </Button>
    </form>
  );
}
