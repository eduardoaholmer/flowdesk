import { ArchiveRestore, Pencil, Trash2 } from "lucide-react";

import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Button } from "@/shared/components/ui/button";

import { useArchiveProject, useDeleteProject, useRestoreProject } from "../hooks";
import type { Project } from "../types";
import { EditProjectDialog } from "./EditProjectDialog";

export function ProjectRowActions({
  workspaceId,
  project,
  onDeleted,
}: {
  workspaceId: string;
  project: Project;
  onDeleted?: () => void;
}) {
  const archiveProject = useArchiveProject(workspaceId);
  const restoreProject = useRestoreProject(workspaceId);
  const deleteProject = useDeleteProject(workspaceId);

  return (
    <div className="flex items-center gap-1">
      <EditProjectDialog
        workspaceId={workspaceId}
        project={project}
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Editar projeto">
            <Pencil />
          </Button>
        }
      />
      {project.status === "ACTIVE" ? (
        <ConfirmActionDialog
          trigger={
            <Button variant="ghost" size="icon-sm" aria-label="Arquivar projeto">
              <ArchiveRestore />
            </Button>
          }
          title="Arquivar projeto?"
          description={`"${project.name}" será marcado como arquivado. Você pode restaurá-lo depois.`}
          confirmLabel="Arquivar"
          isPending={archiveProject.isPending}
          onConfirm={() => archiveProject.mutate(project.id)}
        />
      ) : (
        <ConfirmActionDialog
          trigger={
            <Button variant="ghost" size="icon-sm" aria-label="Restaurar projeto">
              <ArchiveRestore />
            </Button>
          }
          title="Restaurar projeto?"
          description={`"${project.name}" voltará a ficar ativo.`}
          confirmLabel="Restaurar"
          isPending={restoreProject.isPending}
          onConfirm={() => restoreProject.mutate(project.id)}
        />
      )}
      <ConfirmActionDialog
        trigger={
          <Button variant="ghost" size="icon-sm" aria-label="Excluir projeto">
            <Trash2 />
          </Button>
        }
        title="Excluir projeto?"
        description={`"${project.name}" será excluído. Projetos com issues ativas vinculadas não podem ser excluídos.`}
        confirmLabel="Excluir"
        destructive
        isPending={deleteProject.isPending}
        onConfirm={() =>
          deleteProject.mutate(project.id, {
            onSuccess: onDeleted,
          })
        }
      />
    </div>
  );
}
