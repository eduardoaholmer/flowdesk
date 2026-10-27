import { http, HttpResponse } from "msw";

import type { GitHubInstallation } from "@/features/github/types";

import { API_BASE_URL } from "../apiBaseUrl";
import { demoMember } from "../fixtures";

export const demoGitHubInstallation: GitHubInstallation = {
  id: "gh-installation-1",
  installation_id: 4242,
  account_login: "acme-org",
  account_type: "Organization",
  connected_by_id: demoMember.user.id,
  suspended_at: null,
  created_at: "2026-10-27T12:00:00Z",
};

export const githubHandlers = [
  // Sem PR vinculado por padrão: o rail da issue faz esta chamada em todo teste
  // que renderiza o detalhe, e `onUnhandledRequest: "error"` quebraria todos eles.
  http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/github-links`, () =>
    HttpResponse.json({ data: [] }),
  ),

  http.get(`${API_BASE_URL}/workspaces/:workspaceId/integrations/github`, () =>
    HttpResponse.json({ data: { configured: true, installations: [demoGitHubInstallation] } }),
  ),

  http.post(`${API_BASE_URL}/workspaces/:workspaceId/integrations/github/connect`, () =>
    HttpResponse.json({
      data: {
        install_url: "https://github.com/apps/flowdesk/installations/new?state=mock-state",
      },
    }),
  ),

  http.delete(
    `${API_BASE_URL}/workspaces/:workspaceId/integrations/github/installations/:installationId`,
    () => new HttpResponse(null, { status: 204 }),
  ),
];
