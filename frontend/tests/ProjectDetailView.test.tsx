import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ProjectDetailView } from "@/features/projects/components/ProjectDetailView";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { buildPaginationMeta, demoIssue, demoProject } from "./mocks/fixtures";
import { server } from "./mocks/server";

function renderView() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProjectDetailView workspaceId="workspace-1" workspaceSlug="acme" projectId="project-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ProjectDetailView", () => {
  it("shows the project's issues, filtered by project_id", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/projects/:projectId`, () =>
        HttpResponse.json({ data: demoProject }),
      ),
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues`, ({ request }) => {
        const projectId = new URL(request.url).searchParams.get("project_id");
        expect(projectId).toBe("project-1");
        return HttpResponse.json({ data: [demoIssue], meta: buildPaginationMeta(1, 20, 1) });
      }),
    );

    renderView();

    expect(await screen.findByText(demoIssue.title)).toBeInTheDocument();
  });

  it("shows an empty state when the project has no issues", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/projects/:projectId`, () =>
        HttpResponse.json({ data: demoProject }),
      ),
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues`, () =>
        HttpResponse.json({ data: [], meta: buildPaginationMeta(1, 20, 0) }),
      ),
    );

    renderView();

    expect(await screen.findByText("Nenhuma issue ainda")).toBeInTheDocument();
  });
});
