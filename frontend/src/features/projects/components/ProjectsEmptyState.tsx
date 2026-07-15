import { FolderKanban } from "lucide-react";

import { EmptyState } from "@/shared/components/feedback/EmptyState";

import { CreateProjectDialog } from "./CreateProjectDialog";

export function ProjectsEmptyState({
  workspaceId,
  hasFilters,
}: {
  workspaceId: string;
  hasFilters: boolean;
}) {
  return (
    <EmptyState
      icon={FolderKanban}
      title={hasFilters ? "Nenhum projeto encontrado" : "Nenhum projeto ainda"}
      description={
        hasFilters ? "Ajuste a busca ou os filtros." : "Crie o primeiro projeto deste workspace."
      }
      action={!hasFilters && <CreateProjectDialog workspaceId={workspaceId} />}
    />
  );
}
