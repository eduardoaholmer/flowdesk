import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";

import { useDeleteWorkspace, useUpdateWorkspace, useWorkspaceDetail } from "../hooks";

const schema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres."),
  slug: z
    .string()
    .min(2, "O slug deve ter ao menos 2 caracteres.")
    .regex(/^[a-z0-9-]+$/, "Use apenas letras minúsculas, números e hífen."),
  description: z.string().max(280).optional(),
});

type Values = z.infer<typeof schema>;

export function WorkspaceGeneralSettings({
  workspaceId,
  canEdit,
  canDelete,
}: {
  workspaceId: string;
  canEdit: boolean;
  canDelete: boolean;
}) {
  const navigate = useNavigate();
  const { data: workspace, isLoading } = useWorkspaceDetail(workspaceId);
  const updateWorkspace = useUpdateWorkspace(workspaceId);
  const deleteWorkspace = useDeleteWorkspace(workspaceId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    values: workspace
      ? { name: workspace.name, slug: workspace.slug, description: workspace.description ?? "" }
      : undefined,
  });

  useEffect(() => {
    if (workspace) {
      reset({
        name: workspace.name,
        slug: workspace.slug,
        description: workspace.description ?? "",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspace?.id]);

  async function onSubmit(values: Values) {
    await updateWorkspace.mutateAsync({
      name: values.name,
      slug: values.slug,
      description: values.description || undefined,
    });
  }

  async function handleDelete() {
    await deleteWorkspace.mutateAsync();
    navigate("/", { replace: true });
  }

  if (isLoading || !workspace) {
    return (
      <div className="flex flex-col gap-3">
        <div className="h-9 w-full max-w-sm animate-pulse rounded-md bg-muted" />
        <div className="h-9 w-full max-w-sm animate-pulse rounded-md bg-muted" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <form className="flex max-w-lg flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <fieldset disabled={!canEdit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="workspace-name">Nome</Label>
            <Input id="workspace-name" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="workspace-slug">Slug</Label>
            <Input id="workspace-slug" {...register("slug")} />
            {errors.slug && <p className="text-xs text-destructive">{errors.slug.message}</p>}
            <p className="text-xs text-muted-foreground">
              Usado na URL de todas as páginas deste workspace.
            </p>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="workspace-description">Descrição</Label>
            <Textarea id="workspace-description" {...register("description")} />
          </div>
        </fieldset>
        {canEdit && (
          <div>
            <Button type="submit" disabled={!isDirty || updateWorkspace.isPending}>
              {updateWorkspace.isPending ? "Salvando…" : "Salvar alterações"}
            </Button>
          </div>
        )}
      </form>

      {canDelete && (
        <div className="flex max-w-lg flex-col gap-3 rounded-lg border border-destructive/30 p-4">
          <div>
            <h3 className="text-sm font-medium">Excluir workspace</h3>
            <p className="text-sm text-muted-foreground">
              Remove permanentemente o workspace e todo o seu conteúdo. Esta ação não pode ser
              desfeita.
            </p>
          </div>
          <div>
            <ConfirmActionDialog
              trigger={
                <Button variant="destructive" size="sm">
                  Excluir workspace
                </Button>
              }
              title="Excluir este workspace?"
              description={`"${workspace.name}" e todo o seu conteúdo (projetos, issues, comentários) serão excluídos permanentemente.`}
              confirmLabel="Excluir workspace"
              destructive
              isPending={deleteWorkspace.isPending}
              onConfirm={handleDelete}
            />
          </div>
        </div>
      )}
    </div>
  );
}
