import { Link } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { formatRelativeTime } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";
import { cn } from "@/shared/lib/utils";

import type { Notification } from "../types";

const VERBS: Record<Notification["type"], string> = {
  MENTION: "mencionou você em",
  STATUS_CHANGE: "mudou o status de",
  ASSIGNMENT: "atribuiu a você",
};

/** Linha secundária — só existe dado que já vem no payload hoje (sem `issue.title`
 * no contrato de notificação, diferente do handoff): preview da menção, ou a
 * transição de status. `ASSIGNMENT` não tem contexto extra além do próprio verbo. */
function secondaryLine(notification: Notification): string | null {
  const { payload } = notification;
  if (notification.type === "MENTION" && payload.preview) return payload.preview;
  if (notification.type === "STATUS_CHANGE" && payload.old_status && payload.new_status) {
    return `${payload.old_status} → ${payload.new_status}`;
  }
  return null;
}

export function NotificationItem({
  notification,
  workspaceSlug,
  onOpen,
}: {
  notification: Notification;
  workspaceSlug: string | null;
  onOpen: (notification: Notification) => void;
}) {
  const isUnread = notification.read_at === null;
  const issueId = notification.payload.issue_id;
  const actorName = notification.payload.actor_name ?? "Alguém";
  const issueIdentifier = notification.payload.issue_identifier ?? "uma issue";
  const secondary = secondaryLine(notification);
  const content = (
    <div
      className={cn(
        "flex items-start gap-2.5 rounded-md p-2 text-left text-sm",
        isUnread && "bg-sunken",
      )}
    >
      <Avatar size="sm" className="mt-0.5 border border-border2 bg-sunken">
        <AvatarFallback className="bg-transparent text-[9px] font-semibold text-t2">
          {getInitials(actorName)}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <p className="leading-relaxed text-t2">
          <span className="font-semibold text-foreground">{actorName}</span>{" "}
          {VERBS[notification.type]}{" "}
          <span className="font-semibold text-foreground">{issueIdentifier}</span>
        </p>
        {secondary && <p className="truncate text-xs text-t3">{secondary}</p>}
        <p className="mt-0.5 text-xs text-t3">{formatRelativeTime(notification.created_at)}</p>
      </div>
      {isUnread && <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-destructive" />}
    </div>
  );

  if (workspaceSlug && issueId) {
    return (
      <Link
        to={workspaceRoutes.issueDetail(workspaceSlug, issueId)}
        onClick={() => onOpen(notification)}
        className="block rounded-md hover:bg-sunken"
      >
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onOpen(notification)}
      className="block w-full rounded-md hover:bg-muted"
    >
      {content}
    </button>
  );
}
