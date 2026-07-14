import { FolderKanban } from "lucide-react";

import { CreateProjectDialog } from "./CreateProjectDialog";

export function ProjectsEmptyState({
  workspaceId,
  hasFilters,
}: {
  workspaceId: string;
  hasFilters: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
      <FolderKanban className="size-8 text-muted-foreground" />
      {hasFilters ? (
        <div>
          <p className="text-sm font-medium">Nenhum projeto encontrado</p>
          <p className="text-sm text-muted-foreground">Ajuste a busca ou os filtros.</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div>
            <p className="text-sm font-medium">Nenhum projeto ainda</p>
            <p className="text-sm text-muted-foreground">
              Crie o primeiro projeto deste workspace.
            </p>
          </div>
          <CreateProjectDialog workspaceId={workspaceId} />
        </div>
      )}
    </div>
  );
}
