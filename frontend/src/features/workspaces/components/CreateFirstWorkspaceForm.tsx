import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { workspaceRoutes } from "@/shared/lib/routes";

import { useCreateWorkspace } from "../hooks";

const schema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres."),
});

type Values = z.infer<typeof schema>;

export function CreateFirstWorkspaceForm() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) });
  const createWorkspace = useCreateWorkspace();

  async function onSubmit(values: Values) {
    const workspace = await createWorkspace.mutateAsync(values.name);
    navigate(workspaceRoutes.projects(workspace.slug), { replace: true });
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="workspace-name">Nome do workspace</Label>
        <Input id="workspace-name" placeholder="Acme Inc" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <Button type="submit" disabled={createWorkspace.isPending}>
        {createWorkspace.isPending ? "Criando…" : "Criar workspace"}
      </Button>
    </form>
  );
}
