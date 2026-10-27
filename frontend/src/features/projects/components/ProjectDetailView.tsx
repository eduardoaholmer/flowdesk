import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useIssues } from "@/features/issues/hooks";
import { IssuesEmptyState } from "@/features/issues/components/IssuesEmptyState";
import { IssuesTable } from "@/features/issues/components/IssuesTable";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { Pagination } from "@/shared/components/navigation/Pagination";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { formatDate } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";

import { useProject } from "../hooks";
import { ProjectRowActions } from "./ProjectRowActions";
import { ProjectStatusBadge } from "./ProjectStatusBadge";

const ISSUES_PER_PAGE = 20;

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
  const [page, setPage] = useState(1);
  const issuesQuery = useIssues(workspaceId, {
    page,
    per_page: ISSUES_PER_PAGE,
    project_id: projectId,
    sort: "-updated_at",
  });

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
          onDeleted={() => navigate(workspaceRoutes.projects(workspaceSlug), { replace: true })}
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

      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-muted-foreground">Issues</h2>
          {issuesQuery.data && (
            <span className="text-xs text-t3">{issuesQuery.data.meta.total} issues</span>
          )}
        </div>

        {issuesQuery.isLoading ? (
          <ListSkeleton rows={5} />
        ) : issuesQuery.isError ? (
          <ErrorState
            message="Não foi possível carregar as issues do projeto."
            onRetry={() => issuesQuery.refetch()}
          />
        ) : issuesQuery.data && issuesQuery.data.data.length > 0 ? (
          <>
            <IssuesTable
              workspaceId={workspaceId}
              workspaceSlug={workspaceSlug}
              issues={issuesQuery.data.data}
              showProject={false}
            />
            <Pagination meta={issuesQuery.data.meta} itemLabel="issue" onPageChange={setPage} />
          </>
        ) : (
          <IssuesEmptyState hasFilters={false} />
        )}
      </div>
    </div>
  );
}
