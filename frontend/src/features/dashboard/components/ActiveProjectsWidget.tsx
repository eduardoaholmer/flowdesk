import { FolderKanban } from "lucide-react";
import { Link } from "react-router-dom";

import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";
import { useProjects } from "@/features/projects/hooks";
import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { formatDate } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { DashboardWidgetCard } from "./DashboardWidgetCard";

const WIDGET_PAGE_SIZE = 4;

/**
 * Sem barra de progresso (issues concluídas/total por projeto) do handoff: o
 * `ProjectResponse` do backend não expõe contagem de issues por projeto — mudança
 * de contrato fora do escopo desta sub-sprint visual, mesmo padrão de deferimento
 * de `IssueBoardCard`/labels e `IssueDetailView`/rich-text (ADR-045/046, M7).
 */
export function ActiveProjectsWidget({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const { data, isLoading, isError, refetch } = useProjects(workspaceId, {
    page: 1,
    per_page: WIDGET_PAGE_SIZE,
    status: "ACTIVE",
    sort: "-updated_at",
  });
  const { data: members } = useWorkspaceMembers(workspaceId);
  const memberById = new Map((members ?? []).map((member) => [member.user.id, member.user]));

  return (
    <DashboardWidgetCard
      title="Projetos ativos"
      action={
        <Link
          to={workspaceRoutes.projects(workspaceSlug)}
          className="text-xs text-t3 hover:text-foreground"
        >
          Ver todos
        </Link>
      }
    >
      {isLoading ? (
        <div className="p-4">
          <ListSkeleton rows={WIDGET_PAGE_SIZE} />
        </div>
      ) : isError ? (
        <div className="p-4">
          <ErrorState message="Não foi possível carregar os projetos." onRetry={() => refetch()} />
        </div>
      ) : data && data.data.length > 0 ? (
        <ul>
          {data.data.map((project) => {
            const lead = project.lead_id ? memberById.get(project.lead_id) : undefined;
            return (
              <li key={project.id} className="border-b border-border last:border-b-0">
                <Link
                  to={workspaceRoutes.projectDetail(workspaceSlug, project.id)}
                  className="flex items-center gap-3 px-4 py-2.5 hover:bg-sunken"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13px] font-medium">{project.name}</span>
                    <span className="block truncate text-[11.5px] text-t3">
                      {project.description || "Sem descrição"}
                    </span>
                  </span>
                  <span className="shrink-0 text-[11.5px] text-t3">
                    {project.target_date ? formatDate(project.target_date) : "—"}
                  </span>
                  {lead && (
                    <span className="flex size-6 shrink-0 items-center justify-center rounded-full border border-border2 bg-sunken text-[8.5px] font-semibold text-t2">
                      {getInitials(lead.name)}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="p-4">
          <EmptyState
            className="border-none py-10"
            icon={FolderKanban}
            title="Nenhum projeto ativo"
            description="Agrupe issues por objetivo para enxergar progresso."
            action={<CreateProjectDialog workspaceId={workspaceId} />}
          />
        </div>
      )}
    </DashboardWidgetCard>
  );
}
