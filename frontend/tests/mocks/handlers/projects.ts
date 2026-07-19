import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";
import { buildPaginationMeta, demoProject } from "../fixtures";

export const projectsHandlers = [
  http.get(`${API_BASE_URL}/workspaces/:workspaceId/projects`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const perPage = Number(url.searchParams.get("per_page") ?? 20);
    return HttpResponse.json({
      data: [demoProject],
      meta: buildPaginationMeta(page, perPage, 1),
    });
  }),
];
