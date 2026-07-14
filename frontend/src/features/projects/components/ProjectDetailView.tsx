import { useNavigate } from "react-router-dom";

import { ErrorState } from "@/shared/components/ErrorState";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { formatDate } from "@/shared/lib/date";

import { useProject } from "../hooks";
import { ProjectRowActions } from "./ProjectRowActions";
import { ProjectStatusBadge } from "./ProjectStatusBadge";

export function ProjectDetailView({
  workspaceId,
  workspaceSlug,
  projectId,
}: {
  workspaceId: string;
  workspaceSlug: string;
  projectId: string;
}) {
  const navigate = useNavigate();
  const { data: project, isLoading, isError, refetch } = useProject(workspaceId, projectId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full max-w-md" />
        <Skeleton className="h-4 w-full max-w-sm" />
      </div>
    );
  }

  if (isError || !project) {
    return (
      <ErrorState message="Projeto não encontrado ou indisponível." onRetry={() => refetch()} />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          {project.color && (
            <span
              className="inline-block size-3 shrink-0 rounded-full"
              style={{ backgroundColor: project.color }}
            />
          )}
          {project.icon && (
            <span aria-hidden className="text-xl">
              {project.icon}
            </span>
          )}
          <div>
            <h1 className="text-lg font-semibold">{project.name}</h1>
            <p className="text-xs text-muted-foreground">{project.slug}</p>
          </div>
          <ProjectStatusBadge status={project.status} />
        </div>
        <ProjectRowActions
          workspaceId={workspaceId}
          project={project}
          onDeleted={() => navigate(`/w/${workspaceSlug}/projects`, { replace: true })}
        />
      </div>

      <div>
        <h2 className="mb-1 text-sm font-medium text-muted-foreground">Descrição</h2>
        <p className="text-sm">{project.description || "Sem descrição."}</p>
      </div>

      <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted-foreground">Criado em</dt>
          <dd>{formatDate(project.created_at)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Atualizado em</dt>
          <dd>{formatDate(project.updated_at)}</dd>
        </div>
        {project.target_date && (
          <div>
            <dt className="text-muted-foreground">Data alvo</dt>
            <dd>{formatDate(project.target_date)}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}
