import { useDraggable } from "@dnd-kit/core";
import { Link } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { IssuePriorityBadge } from "./IssuePriorityBadge";
import type { Issue } from "../types";

function IssueBoardCardContent({
  issue,
  assigneeName,
}: {
  issue: Issue;
  assigneeName: string | undefined;
}) {
  return (
    <>
      <p className="font-mono text-xs text-muted-foreground">{issue.identifier}</p>
      <p className="line-clamp-2 font-medium">{issue.title}</p>
      <div className="flex items-center justify-between">
        <IssuePriorityBadge priority={issue.priority} />
        {assigneeName && (
          <Avatar className="size-5">
            <AvatarFallback className="text-[10px]">{getInitials(assigneeName)}</AvatarFallback>
          </Avatar>
        )}
      </div>
    </>
  );
}

export function IssueBoardCard({
  workspaceSlug,
  issue,
  assigneeName,
}: {
  workspaceSlug: string;
  issue: Issue;
  assigneeName: string | undefined;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: issue.id });

  return (
    <Link
      ref={setNodeRef}
      to={workspaceRoutes.issueDetail(workspaceSlug, issue.id)}
      className="flex flex-col gap-2 rounded-lg border bg-card p-3 text-sm hover:border-ring"
      style={{ opacity: isDragging ? 0.4 : 1, touchAction: "none" }}
      {...attributes}
      {...listeners}
    >
      <IssueBoardCardContent issue={issue} assigneeName={assigneeName} />
    </Link>
  );
}

/** Clone puramente visual usado dentro de `DragOverlay` (`IssuesBoardView`) —
 * não chama `useDraggable`, já que o card original (ainda montado na coluna)
 * já registra o mesmo `issue.id` como draggable; registrar duas vezes o
 * mesmo id corromperia o registro interno do dnd-kit. */
export function IssueBoardCardPreview({
  issue,
  assigneeName,
}: {
  issue: Issue;
  assigneeName: string | undefined;
}) {
  return (
    <div className="flex w-64 flex-col gap-2 rounded-lg border bg-card p-3 text-sm shadow-lg">
      <IssueBoardCardContent issue={issue} assigneeName={assigneeName} />
    </div>
  );
}
