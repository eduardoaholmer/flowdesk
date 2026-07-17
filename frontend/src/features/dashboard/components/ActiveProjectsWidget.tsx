import { FolderKanban } from "lucide-react";
import { Link } from "react-router-dom";

import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";
import { useProjects } from "@/features/projects/hooks";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Button } from "@/shared/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { formatDate } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";

const WIDGET_PAGE_SIZE = 5;

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Projetos ativos</CardTitle>
        <CardAction>
          <Button variant="ghost" size="sm" asChild>
            <Link to={workspaceRoutes.projects(workspaceSlug)}>Ver todos</Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <ListSkeleton rows={WIDGET_PAGE_SIZE} />
        ) : isError ? (
          <ErrorState message="Não foi possível carregar os projetos." onRetry={() => refetch()} />
        ) : data && data.data.length > 0 ? (
          <ul className="flex flex-col divide-y">
            {data.data.map((project) => (
              <li
                key={project.id}
                className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
              >
                <Link
                  to={workspaceRoutes.projectDetail(workspaceSlug, project.id)}
                  className="min-w-0 flex-1 truncate text-sm font-medium hover:underline"
                >
                  {project.name}
                </Link>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {project.target_date ? formatDate(project.target_date) : "Sem data alvo"}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={FolderKanban}
            title="Nenhum projeto ativo"
            description="Crie um projeto para agrupar issues relacionadas."
            action={<CreateProjectDialog workspaceId={workspaceId} />}
          />
        )}
      </CardContent>
    </Card>
  );
}
