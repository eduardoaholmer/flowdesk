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
import { ChevronRight } from "lucide-react";
import { useState } from "react";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { useWorkflowStates } from "@/features/workflow-states/hooks";
import type { WorkflowState } from "@/features/workflow-states/types";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { KanbanSkeleton } from "@/shared/components/skeletons/KanbanSkeleton";
import { Button } from "@/shared/components/ui/button";
import { useLocalStorage } from "@/shared/hooks/useLocalStorage";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";
import { cn } from "@/shared/lib/utils";

import { useIssues, useMoveIssueStatus } from "../hooks";
import type { Issue } from "../types";
import { IssueBoardCard, IssueBoardCardPreview } from "./IssueBoardCard";
import { IssueStatusIcon } from "./IssueStatusIcon";

const BOARD_LIST_PARAMS = { page: 1, per_page: MAX_PICKER_PAGE_SIZE, sort: "-updated_at" } as const;

function BoardColumn({ stateId, children }: { stateId: string; children: React.ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id: stateId });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex min-h-16 flex-1 flex-col gap-2 rounded-lg border border-transparent p-1 transition-colors",
        isOver && "border-border2 bg-sunken",
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
  const { data: workflowStates, isLoading: isLoadingStates } = useWorkflowStates(workspaceId);
  const moveIssueStatus = useMoveIssueStatus(workspaceId, BOARD_LIST_PARAMS);
  const [activeIssue, setActiveIssue] = useState<Issue | null>(null);
  const [collapsedColumns, setCollapsedColumns] = useLocalStorage<string[]>(
    `flowdesk:board-collapsed-columns:${workspaceId}`,
    [],
  );
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const memberById = new Map((members ?? []).map((member) => [member.user.id, member.user]));

  const header = (
    <div>
      <h1 className="text-lg font-semibold">Board</h1>
      <p className="text-sm text-muted-foreground">
        Arraste cartões entre colunas para mudar o status.
      </p>
    </div>
  );

  if (isLoading || isLoadingStates) {
    return (
      <div className="flex flex-col gap-4">
        {header}
        <KanbanSkeleton columns={workflowStates?.length ?? 5} />
      </div>
    );
  }
  if (isError || !data || !workflowStates) {
    return (
      <div className="flex flex-col gap-4">
        {header}
        <ErrorState message="Não foi possível carregar o board." onRetry={() => refetch()} />
      </div>
    );
  }

  const issuesByStatus = new Map<string, Issue[]>(workflowStates.map((state) => [state.id, []]));
  for (const issue of data.data) {
    issuesByStatus.get(issue.status_id)?.push(issue);
  }

  function toggleColumn(stateId: string) {
    setCollapsedColumns((previous) =>
      previous.includes(stateId) ? previous.filter((id) => id !== stateId) : [...previous, stateId],
    );
  }

  function handleDragStart(event: DragStartEvent) {
    const issue = data?.data.find((candidate) => candidate.id === event.active.id);
    setActiveIssue(issue ?? null);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveIssue(null);
    const targetStateId = event.over?.id as string | undefined;
    const issue = data?.data.find((candidate) => candidate.id === event.active.id);
    const targetState = workflowStates?.find((state) => state.id === targetStateId);
    if (!issue || !targetState || issue.status_id === targetState.id) {
      return;
    }
    moveIssueStatus.mutate({
      issueId: issue.id,
      statusId: targetState.id,
      statusName: targetState.name,
    });
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setActiveIssue(null)}
    >
      <div className="mb-4">{header}</div>
      <div className="flex gap-4 overflow-x-auto pb-2">
        {workflowStates.map((state) => {
          const columnIssues = issuesByStatus.get(state.id) ?? [];
          const collapsed = collapsedColumns.includes(state.id);
          return (
            <BoardColumnShell
              key={state.id}
              state={state}
              count={columnIssues.length}
              collapsed={collapsed}
              onToggle={() => toggleColumn(state.id)}
            >
              <BoardColumn stateId={state.id}>
                {columnIssues.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-border2 px-2.5 py-4 text-center text-xs text-muted-foreground">
                    Solte um cartão aqui
                  </p>
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
            </BoardColumnShell>
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

function BoardColumnShell({
  state,
  count,
  collapsed,
  onToggle,
  children,
}: {
  state: WorkflowState;
  count: number;
  collapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  if (collapsed) {
    return (
      <div
        data-slot="board-column"
        data-status={state.id}
        className="flex w-10 shrink-0 flex-col items-center gap-2 pt-1"
      >
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={`Expandir coluna ${state.name}`}
          onClick={onToggle}
        >
          <ChevronRight />
        </Button>
        <IssueStatusIcon category={state.category} />
        <span className="text-xs text-t3">{count}</span>
      </div>
    );
  }

  return (
    <div
      data-slot="board-column"
      data-status={state.id}
      className="flex w-64 shrink-0 flex-col gap-2"
    >
      <div className="flex items-center gap-2 px-1">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={`Recolher coluna ${state.name}`}
          className="-ml-1"
          onClick={onToggle}
        >
          <ChevronRight className="rotate-180" />
        </Button>
        <IssueStatusIcon category={state.category} />
        <h2 className="text-[12.5px] font-semibold">{state.name}</h2>
        <span className="text-xs text-t3">{count}</span>
      </div>
      {children}
    </div>
  );
}
