import { Bell } from "lucide-react";
import { Link } from "react-router-dom";

import { useMarkNotificationRead, useRecentNotifications } from "@/features/notifications/hooks";
import type { Notification } from "@/features/notifications/types";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { formatRelativeTime } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { DashboardWidgetCard } from "./DashboardWidgetCard";

const WIDGET_ITEM_LIMIT = 5;

/** Texto do verbo por tipo de notificação — mesma redação de `NotificationItem::describe`,
 * só reorganizada em partes (ator/verbo/issue) para o layout de linha do handoff. */
function describeAction(notification: Notification): { verb: string; subtitle?: string } {
  const { payload } = notification;
  if (notification.type === "MENTION") {
    return { verb: "mencionou você em", subtitle: payload.preview };
  }
  if (notification.type === "STATUS_CHANGE") {
    return { verb: `mudou o status para ${payload.new_status ?? "novo status"} em` };
  }
  return { verb: "atribuiu a você" };
}

export function RecentActivityWidget({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const { data, isLoading, isError, refetch } = useRecentNotifications();
  const markRead = useMarkNotificationRead();

  function handleOpen(notification: Notification) {
    if (notification.read_at === null) {
      markRead.mutate(notification.id);
    }
  }

  const workspaceNotifications =
    data?.data.filter((notification) => notification.workspace_id === workspaceId) ?? [];

  return (
    <DashboardWidgetCard title="Atividade recente">
      {isLoading ? (
        <div className="p-4">
          <ListSkeleton rows={WIDGET_ITEM_LIMIT} />
        </div>
      ) : isError ? (
        <div className="p-4">
          <ErrorState
            message="Não foi possível carregar a atividade recente."
            onRetry={() => refetch()}
          />
        </div>
      ) : workspaceNotifications.length > 0 ? (
        <ul>
          {workspaceNotifications.slice(0, WIDGET_ITEM_LIMIT).map((notification) => {
            const actorName = notification.payload.actor_name ?? "Alguém";
            const issueIdentifier = notification.payload.issue_identifier;
            const issueId = notification.payload.issue_id;
            const { verb, subtitle } = describeAction(notification);
            const content = (
              <div className="flex items-start gap-2.5 px-4 py-2.5 hover:bg-sunken">
                <span className="mt-px flex size-6 shrink-0 items-center justify-center rounded-full border border-border2 bg-sunken text-[8.5px] font-semibold text-t2">
                  {getInitials(actorName)}
                </span>
                <span className="min-w-0 flex-1 text-[12.5px] leading-relaxed text-t2">
                  <b className="font-semibold text-foreground">{actorName}</b> {verb}
                  {issueIdentifier ? ` ${issueIdentifier}` : ""}
                  {subtitle && (
                    <span className="block truncate text-[11.5px] text-t3">{subtitle}</span>
                  )}
                </span>
                <span className="shrink-0 text-[11px] text-t3">
                  {formatRelativeTime(notification.created_at)}
                </span>
              </div>
            );
            return (
              <li key={notification.id} className="border-b border-border last:border-b-0">
                {issueId ? (
                  <Link
                    to={workspaceRoutes.issueDetail(workspaceSlug, issueId)}
                    onClick={() => handleOpen(notification)}
                  >
                    {content}
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="w-full text-left"
                    onClick={() => handleOpen(notification)}
                  >
                    {content}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="p-4">
          <EmptyState
            className="border-none py-10"
            icon={Bell}
            title="Nenhuma atividade recente"
            description="A atividade do time aparece aqui conforme o trabalho acontece."
          />
        </div>
      )}
    </DashboardWidgetCard>
  );
}
