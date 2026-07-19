import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ActiveProjectsWidget } from "@/features/dashboard/components/ActiveProjectsWidget";
import type { Project } from "@/features/projects/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { buildPaginationMeta } from "./mocks/fixtures";
import { server } from "./mocks/server";

function renderWidget() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ActiveProjectsWidget workspaceId="ws-1" workspaceSlug="acme" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const baseProject: Project = {
  id: "project-1",
  workspace_id: "ws-1",
  name: "Ring Gate",
  slug: "ring-gate",
  description: null,
  icon: null,
  color: null,
  status: "ACTIVE",
  target_date: null,
  lead_id: null,
  created_by: "user-1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("ActiveProjectsWidget", () => {
  it("shows active projects and requests only the ACTIVE status", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/projects`, ({ request }) => {
        const status = new URL(request.url).searchParams.get("status");
        if (status !== "ACTIVE") {
          return HttpResponse.json({ data: [], meta: buildPaginationMeta(1, 5, 0) });
        }
        return HttpResponse.json({ data: [baseProject], meta: buildPaginationMeta(1, 5, 1) });
      }),
    );

    renderWidget();

    expect(await screen.findByText("Ring Gate")).toBeInTheDocument();
  });

  it("shows an empty state when there are no active projects", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/projects`, () =>
        HttpResponse.json({ data: [], meta: buildPaginationMeta(1, 5, 0) }),
      ),
    );

    renderWidget();

    expect(await screen.findByText("Nenhum projeto ativo")).toBeInTheDocument();
  });
});
