import { ArrowRightLeft, AtSign, Bell } from "lucide-react";
import { Link } from "react-router-dom";

import { formatDateTime } from "@/shared/lib/date";
import { cn } from "@/shared/lib/utils";
import { workspaceRoutes } from "@/shared/lib/routes";

import type { Notification } from "../types";

function describe(notification: Notification): string {
  const { payload } = notification;
  if (notification.type === "MENTION") {
    return `${payload.actor_name ?? "Alguém"} mencionou você em ${payload.issue_identifier ?? "uma issue"}`;
  }
  if (notification.type === "STATUS_CHANGE") {
    return `${payload.actor_name ?? "Alguém"} mudou ${payload.issue_identifier ?? "uma issue"} para ${payload.new_status ?? "novo status"}`;
  }
  return "Nova notificação";
}

const ICONS: Record<Notification["type"], typeof Bell> = {
  MENTION: AtSign,
  STATUS_CHANGE: ArrowRightLeft,
  ASSIGNMENT: Bell,
};

export function NotificationItem({
  notification,
  workspaceSlug,
  onOpen,
}: {
  notification: Notification;
  workspaceSlug: string | null;
  onOpen: (notification: Notification) => void;
}) {
  const Icon = ICONS[notification.type];
  const isUnread = notification.read_at === null;
  const issueId = notification.payload.issue_id;
  const content = (
    <div
      className={cn(
        "flex items-start gap-2.5 rounded-md p-2 text-left text-sm",
        isUnread && "bg-muted/50",
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className={cn("truncate", isUnread && "font-medium")}>{describe(notification)}</p>
        <p className="text-xs text-muted-foreground">{formatDateTime(notification.created_at)}</p>
      </div>
      {isUnread && <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />}
    </div>
  );

  if (workspaceSlug && issueId) {
    return (
      <Link
        to={workspaceRoutes.issueDetail(workspaceSlug, issueId)}
        onClick={() => onOpen(notification)}
        className="block rounded-md hover:bg-muted"
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
