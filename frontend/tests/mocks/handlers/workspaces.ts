import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";
import { buildPaginationMeta, demoInvitation, demoMember } from "../fixtures";

export const workspacesHandlers = [
  http.get(`${API_BASE_URL}/workspaces/:workspaceId/members`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const perPage = Number(url.searchParams.get("per_page") ?? 20);
    return HttpResponse.json({
      data: [demoMember],
      meta: buildPaginationMeta(page, perPage, 1),
    });
  }),

  http.patch(
    `${API_BASE_URL}/workspaces/:workspaceId/members/:memberId`,
    async ({ params, request }) => {
      const body = (await request.json()) as { role: string };
      return HttpResponse.json({
        data: { ...demoMember, id: params.memberId as string, role: body.role },
      });
    },
  ),

  http.delete(
    `${API_BASE_URL}/workspaces/:workspaceId/members/:memberId`,
    () => new HttpResponse(null, { status: 204 }),
  ),

  http.get(`${API_BASE_URL}/workspaces/:workspaceId/invitations`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const perPage = Number(url.searchParams.get("per_page") ?? 20);
    return HttpResponse.json({
      data: [demoInvitation],
      meta: buildPaginationMeta(page, perPage, 1),
    });
  }),

  http.post(`${API_BASE_URL}/workspaces/:workspaceId/invitations`, async ({ request }) => {
    const body = (await request.json()) as { email: string; role: string };
    return HttpResponse.json(
      {
        data: {
          ...demoInvitation,
          email: body.email,
          role: body.role,
          token: "mock-invitation-token",
        },
      },
      { status: 201 },
    );
  }),

  http.delete(
    `${API_BASE_URL}/workspaces/:workspaceId/invitations/:invitationId`,
    () => new HttpResponse(null, { status: 204 }),
  ),
];
