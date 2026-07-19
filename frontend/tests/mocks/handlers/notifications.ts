import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";
import { buildPaginationMeta, demoNotification } from "../fixtures";

export const notificationsHandlers = [
  http.get(`${API_BASE_URL}/notifications`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const perPage = Number(url.searchParams.get("per_page") ?? 20);
    return HttpResponse.json({
      data: [demoNotification],
      meta: buildPaginationMeta(page, perPage, 1),
    });
  }),

  http.patch(`${API_BASE_URL}/notifications/:notificationId`, ({ params }) => {
    return HttpResponse.json({
      data: {
        ...demoNotification,
        id: params.notificationId as string,
        read_at: "2026-01-02T00:00:00Z",
      },
    });
  }),

  http.post(
    `${API_BASE_URL}/notifications/mark-all-read`,
    () => new HttpResponse(null, { status: 204 }),
  ),
];
