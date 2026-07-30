import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";

const baseMatrix = [
  { permission: "issue.create", role: "ADMIN", default: true, effective: true, is_override: false },
  {
    permission: "issue.create",
    role: "MEMBER",
    default: true,
    effective: true,
    is_override: false,
  },
  {
    permission: "issue.create",
    role: "GUEST",
    default: false,
    effective: false,
    is_override: false,
  },
];

export const permissionOverridesHandlers = [
  http.get(`${API_BASE_URL}/workspaces/:workspaceId/permission-overrides`, () => {
    return HttpResponse.json({ data: baseMatrix });
  }),
  http.put(`${API_BASE_URL}/workspaces/:workspaceId/permission-overrides`, async ({ request }) => {
    const body = (await request.json()) as { role: string; permission: string; granted: boolean };
    const updated = baseMatrix.map((entry) =>
      entry.role === body.role && entry.permission === body.permission
        ? { ...entry, effective: body.granted, is_override: body.granted !== entry.default }
        : entry,
    );
    return HttpResponse.json({ data: updated });
  }),
];
