import { useDraggable } from "@dnd-kit/core";
import { Link } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { IssuePriorityIcon } from "./IssuePriorityIcon";
import type { Issue } from "../types";

/** Sombra sutil do cartão de board, conforme o handoff de redesign (Milestone 7,
 * `docs/design-handoff/2026-07-20-redesign-gestor/data.js` não cobre isso — vem do
 * `.dc.html` do board diretamente) — one-off, não é o token `--sh` do sistema
 * (esse é reservado a popover/modal/dropdown, mais pronunciado). */
const CARD_SHADOW = { boxShadow: "0 1px 2px rgba(20,19,15,.05)" };

function IssueBoardCardContent({
  issue,
  assigneeName,
}: {
  issue: Issue;
  assigneeName: string | undefined;
}) {
  return (
    <>
      <div className="flex items-center justify-between gap-2">
        <p className="font-mono text-xs text-t3">{issue.identifier}</p>
        <IssuePriorityIcon priority={issue.priority} />
      </div>
      <p className="line-clamp-2 text-[12.5px] leading-snug font-medium">{issue.title}</p>
      <div className="flex items-center justify-end">
        {assigneeName && (
          <Avatar className="size-5 border border-border2 bg-sunken">
            <AvatarFallback className="bg-transparent text-[7.5px] font-semibold text-t2">
              {getInitials(assigneeName)}
            </AvatarFallback>
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
      className="flex cursor-grab flex-col gap-1.5 rounded-lg border border-border bg-panel px-3 py-2.5 text-sm hover:border-border2"
      style={{ ...CARD_SHADOW, opacity: isDragging ? 0.4 : 1, touchAction: "none" }}
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
    <div className="flex w-64 cursor-grab flex-col gap-1.5 rounded-lg border border-border bg-panel px-3 py-2.5 text-sm shadow-lg">
      <IssueBoardCardContent issue={issue} assigneeName={assigneeName} />
    </div>
  );
}
