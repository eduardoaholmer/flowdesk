import { ListTodo } from "lucide-react";
import { Link } from "react-router-dom";

import { CreateIssueDialog } from "@/features/issues/components/CreateIssueDialog";
import { IssuePriorityIcon } from "@/features/issues/components/IssuePriorityIcon";
import { IssueStatusIcon } from "@/features/issues/components/IssueStatusIcon";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { formatDate } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";

import { useMyRadarIssues } from "../hooks";
import { DashboardWidgetCard } from "./DashboardWidgetCard";

export function MyIssuesWidget({
  workspaceId,
  workspaceSlug,
  userId,
}: {
  workspaceId: string;
  workspaceSlug: string;
  userId: string;
}) {
  const { issues, isLoading, isError, refetch } = useMyRadarIssues(workspaceId, userId);

  return (
    <DashboardWidgetCard
      title="Minhas issues"
      action={
        <Link
          to={workspaceRoutes.issues(workspaceSlug)}
          className="text-xs text-t3 hover:text-foreground"
        >
          Ver todas
        </Link>
      }
    >
      {isLoading ? (
        <div className="p-4">
          <ListSkeleton rows={4} />
        </div>
      ) : isError ? (
        <div className="p-4">
          <ErrorState message="Não foi possível carregar suas issues." onRetry={() => refetch()} />
        </div>
      ) : issues.length > 0 ? (
        <ul>
          {issues.map((issue) => (
            <li key={issue.id} className="border-b border-border last:border-b-0">
              <Link
                to={workspaceRoutes.issueDetail(workspaceSlug, issue.id)}
                className="flex h-10 items-center gap-2.5 px-4 hover:bg-sunken"
              >
                <IssuePriorityIcon priority={issue.priority} />
                <IssueStatusIcon status={issue.status} />
                <span className="font-mono text-xs text-t3">{issue.identifier}</span>
                <span className="min-w-0 flex-1 truncate text-[13px] font-medium">
                  {issue.title}
                </span>
                <span className="shrink-0 text-xs text-t3">
                  {issue.due_date ? formatDate(issue.due_date) : "—"}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="p-4">
          <EmptyState
            className="border-none py-10"
            icon={ListTodo}
            title="Nada atribuído a você"
            description="Bom sinal — ou hora de puxar algo do backlog."
            action={<CreateIssueDialog workspaceId={workspaceId} />}
          />
        </div>
      )}
    </DashboardWidgetCard>
  );
}
