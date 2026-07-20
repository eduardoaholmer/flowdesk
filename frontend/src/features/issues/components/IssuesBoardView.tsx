import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCenter,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useState } from "react";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { KanbanSkeleton } from "@/shared/components/skeletons/KanbanSkeleton";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";
import { cn } from "@/shared/lib/utils";

import { ISSUE_STATUS_LABELS } from "../constants";
import { useIssues, useMoveIssueStatus } from "../hooks";
import type { Issue, IssueStatus } from "../types";
import { IssueBoardCard, IssueBoardCardPreview } from "./IssueBoardCard";

const BOARD_COLUMNS = Object.keys(ISSUE_STATUS_LABELS) as IssueStatus[];
const BOARD_LIST_PARAMS = { page: 1, per_page: MAX_PICKER_PAGE_SIZE, sort: "-updated_at" } as const;

function BoardColumn({ status, children }: { status: IssueStatus; children: React.ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id: status });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex min-h-16 flex-col gap-2 rounded-lg p-1 transition-colors",
        isOver && "bg-accent",
      )}
    >
      {children}
    </div>
  );
}

export function IssuesBoardView({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const { data, isLoading, isError, refetch } = useIssues(workspaceId, BOARD_LIST_PARAMS);
  const { data: members } = useWorkspaceMembers(workspaceId);
  const moveIssueStatus = useMoveIssueStatus(workspaceId, BOARD_LIST_PARAMS);
  const [activeIssue, setActiveIssue] = useState<Issue | null>(null);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

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

  function handleDragStart(event: DragStartEvent) {
    const issue = data?.data.find((candidate) => candidate.id === event.active.id);
    setActiveIssue(issue ?? null);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveIssue(null);
    const targetStatus = event.over?.id as IssueStatus | undefined;
    const issue = data?.data.find((candidate) => candidate.id === event.active.id);
    if (!issue || !targetStatus || issue.status === targetStatus) {
      return;
    }
    moveIssueStatus.mutate({ issueId: issue.id, status: targetStatus });
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setActiveIssue(null)}
    >
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
              <BoardColumn status={status}>
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
              </BoardColumn>
            </div>
          );
        })}
      </div>
      <DragOverlay>
        {activeIssue && (
          <IssueBoardCardPreview
            issue={activeIssue}
            assigneeName={
              activeIssue.assignee_id ? memberById.get(activeIssue.assignee_id)?.name : undefined
            }
          />
        )}
      </DragOverlay>
    </DndContext>
  );
}
