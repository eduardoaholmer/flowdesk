import { ListTodo } from "lucide-react";
import { Link } from "react-router-dom";

import { CreateIssueDialog } from "@/features/issues/components/CreateIssueDialog";
import { IssuePriorityBadge } from "@/features/issues/components/IssuePriorityBadge";
import { IssueStatusBadge } from "@/features/issues/components/IssueStatusBadge";
import { useIssues } from "@/features/issues/hooks";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Button } from "@/shared/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { workspaceRoutes } from "@/shared/lib/routes";

const WIDGET_PAGE_SIZE = 5;

export function MyIssuesWidget({
  workspaceId,
  workspaceSlug,
  userId,
}: {
  workspaceId: string;
  workspaceSlug: string;
  userId: string;
}) {
  const { data, isLoading, isError, refetch } = useIssues(workspaceId, {
    page: 1,
    per_page: WIDGET_PAGE_SIZE,
    assignee_id: userId,
    sort: "-updated_at",
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Minhas issues</CardTitle>
        <CardAction>
          <Button variant="ghost" size="sm" asChild>
            <Link to={workspaceRoutes.issues(workspaceSlug)}>Ver todas</Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <ListSkeleton rows={WIDGET_PAGE_SIZE} />
        ) : isError ? (
          <ErrorState message="Não foi possível carregar suas issues." onRetry={() => refetch()} />
        ) : data && data.data.length > 0 ? (
          <ul className="flex flex-col divide-y">
            {data.data.map((issue) => (
              <li
                key={issue.id}
                className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
              >
                <Link
                  to={workspaceRoutes.issueDetail(workspaceSlug, issue.id)}
                  className="min-w-0 flex-1"
                >
                  <span className="mr-2 font-mono text-xs text-muted-foreground">
                    {issue.identifier}
                  </span>
                  <span className="truncate text-sm font-medium hover:underline">
                    {issue.title}
                  </span>
                </Link>
                <div className="flex shrink-0 items-center gap-3">
                  <IssuePriorityBadge priority={issue.priority} />
                  <IssueStatusBadge status={issue.status} />
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={ListTodo}
            title="Nenhuma issue atribuída a você"
            description="Issues atribuídas a você aparecem aqui."
            action={<CreateIssueDialog workspaceId={workspaceId} />}
          />
        )}
      </CardContent>
    </Card>
  );
}
