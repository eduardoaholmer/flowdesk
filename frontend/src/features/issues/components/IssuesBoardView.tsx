import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { KanbanSkeleton } from "@/shared/components/skeletons/KanbanSkeleton";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";

import { ISSUE_STATUS_LABELS } from "../constants";
import { useIssues } from "../hooks";
import type { Issue, IssueStatus } from "../types";
import { IssueBoardCard } from "./IssueBoardCard";

const BOARD_COLUMNS = Object.keys(ISSUE_STATUS_LABELS) as IssueStatus[];

export function IssuesBoardView({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const { data, isLoading, isError, refetch } = useIssues(workspaceId, {
    page: 1,
    per_page: MAX_PICKER_PAGE_SIZE,
    sort: "-updated_at",
  });
  const { data: members } = useWorkspaceMembers(workspaceId);
  const memberById = new Map((members ?? []).map((member) => [member.user.id, member.user]));

  if (isLoading) {
    return <KanbanSkeleton columns={BOARD_COLUMNS.length} />;
  }
  if (isError || !data) {
    return <ErrorState message="Não foi possível carregar o board." onRetry={() => refetch()} />;
  }

  const issuesByStatus = new Map<IssueStatus, Issue[]>(BOARD_COLUMNS.map((status) => [status, []]));
  for (const issue of data.data) {
    issuesByStatus.get(issue.status)?.push(issue);
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-2">
      {BOARD_COLUMNS.map((status) => {
        const columnIssues = issuesByStatus.get(status) ?? [];
        return (
          <div
            key={status}
            data-slot="board-column"
            data-status={status}
            className="flex w-64 shrink-0 flex-col gap-2"
          >
            <div className="flex items-center gap-2 px-1">
              <h2 className="text-sm font-medium">{ISSUE_STATUS_LABELS[status]}</h2>
              <span className="text-xs text-muted-foreground">{columnIssues.length}</span>
            </div>
            <div className="flex flex-col gap-2">
              {columnIssues.length === 0 ? (
                <p className="px-1 text-xs text-muted-foreground">Nenhuma issue</p>
              ) : (
                columnIssues.map((issue) => (
                  <IssueBoardCard
                    key={issue.id}
                    workspaceSlug={workspaceSlug}
                    issue={issue}
                    assigneeName={
                      issue.assignee_id ? memberById.get(issue.assignee_id)?.name : undefined
                    }
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
