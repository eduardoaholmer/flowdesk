import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";
import { buildPaginationMeta, demoIssue } from "../fixtures";

export const issuesHandlers = [
  http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const perPage = Number(url.searchParams.get("per_page") ?? 20);
    return HttpResponse.json({
      data: [demoIssue],
      meta: buildPaginationMeta(page, perPage, 1),
    });
  }),
];
