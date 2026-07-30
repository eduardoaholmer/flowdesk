import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { workspaceRoutes } from "@/shared/lib/routes";
import { useUiStore } from "@/shared/stores/uiStore";

import { useCreateWorkspace } from "../hooks";

const schema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres."),
});

type Values = z.infer<typeof schema>;

/**
 * Montado uma única vez em `AppLayout` (mesmo padrão de `CreateIssueDialog`,
 * Sprint 22.2) — controlado por `uiStore.isCreateWorkspaceOpen`, aberto pelo
 * item "Criar workspace" do `WorkspaceSwitcher`.
 */
export function CreateWorkspaceDialog() {
  const navigate = useNavigate();
  const open = useUiStore((state) => state.isCreateWorkspaceOpen);
  const setOpen = useUiStore((state) => state.setCreateWorkspaceOpen);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) });
  const createWorkspace = useCreateWorkspace();

  async function onSubmit(values: Values) {
    const workspace = await createWorkspace.mutateAsync(values.name);
    reset();
    setOpen(false);
    navigate(workspaceRoutes.projects(workspace.slug));
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Criar workspace</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-1.5 py-4">
            <Label htmlFor="create-workspace-name">Nome do workspace</Label>
            <Input id="create-workspace-name" placeholder="Acme Inc" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createWorkspace.isPending}>
              {createWorkspace.isPending ? "Criando…" : "Criar workspace"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
