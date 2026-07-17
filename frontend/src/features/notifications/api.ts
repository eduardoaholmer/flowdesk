import { httpClient } from "@/shared/lib/httpClient";
import type { CollectionEnvelope, DataEnvelope } from "@/shared/lib/apiTypes";

import type { Notification } from "./types";

export interface NotificationListParams {
  page: number;
  per_page: number;
  read?: boolean;
}

export async function listNotifications(
  params: NotificationListParams,
): Promise<CollectionEnvelope<Notification>> {
  const { data } = await httpClient.get<CollectionEnvelope<Notification>>("/notifications", {
    params,
  });
  return data;
}

export async function markNotificationRead(notificationId: string): Promise<Notification> {
  const { data } = await httpClient.patch<DataEnvelope<Notification>>(
    `/notifications/${notificationId}`,
  );
  return data.data;
}

export async function markAllNotificationsRead(): Promise<void> {
  await httpClient.post("/notifications/mark-all-read");
}
