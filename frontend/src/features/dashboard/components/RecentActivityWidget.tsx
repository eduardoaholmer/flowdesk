import { Bell } from "lucide-react";

import { NotificationItem } from "@/features/notifications/components/NotificationItem";
import { useMarkNotificationRead, useRecentNotifications } from "@/features/notifications/hooks";
import type { Notification } from "@/features/notifications/types";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";

const WIDGET_ITEM_LIMIT = 5;

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
    <Card>
      <CardHeader>
        <CardTitle>Atividade recente</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <ListSkeleton rows={WIDGET_ITEM_LIMIT} />
        ) : isError ? (
          <ErrorState
            message="Não foi possível carregar a atividade recente."
            onRetry={() => refetch()}
          />
        ) : workspaceNotifications.length > 0 ? (
          <div className="flex flex-col gap-0.5">
            {workspaceNotifications.slice(0, WIDGET_ITEM_LIMIT).map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                workspaceSlug={workspaceSlug}
                onOpen={handleOpen}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Bell}
            title="Nenhuma atividade recente"
            description="Menções e mudanças de status neste workspace aparecem aqui."
          />
        )}
      </CardContent>
    </Card>
  );
}
