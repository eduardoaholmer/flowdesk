import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/shared/lib/errors";

import * as api from "./api";

const NOTIFICATIONS_KEY = ["notifications"] as const;

/** Polling simples (sem WebSocket ainda, docs/08-roadmap.md Sprint 10+) — intervalo
 * generoso o bastante para não sobrecarregar a API só para um sino de notificação. */
const POLL_INTERVAL_MS = 30_000;
const RECENT_PAGE_SIZE = 10;

export function useRecentNotifications() {
  return useQuery({
    queryKey: [...NOTIFICATIONS_KEY, "recent"],
    queryFn: () => api.listNotifications({ page: 1, per_page: RECENT_PAGE_SIZE }),
    refetchInterval: POLL_INTERVAL_MS,
    staleTime: 15_000,
  });
}

export function useUnreadNotificationsCount() {
  return useQuery({
    queryKey: [...NOTIFICATIONS_KEY, "unread-count"],
    queryFn: () => api.listNotifications({ page: 1, per_page: 1, read: false }),
    select: (data) => data.meta.total,
    refetchInterval: POLL_INTERVAL_MS,
    staleTime: 15_000,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => api.markNotificationRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY });
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY });
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}
