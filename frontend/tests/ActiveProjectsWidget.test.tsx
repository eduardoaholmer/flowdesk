import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ActiveProjectsWidget } from "@/features/dashboard/components/ActiveProjectsWidget";
import type { Project } from "@/features/projects/types";
import type { CollectionEnvelope } from "@/shared/lib/apiTypes";

const { listProjectsMock } = vi.hoisted(() => ({ listProjectsMock: vi.fn() }));

vi.mock("@/features/projects/api", () => ({
  listProjects: listProjectsMock,
}));

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
    listProjectsMock.mockResolvedValue({
      data: [baseProject],
      meta: { page: 1, per_page: 5, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<Project>);

    renderWidget();

    expect(await screen.findByText("Ring Gate")).toBeInTheDocument();
    expect(listProjectsMock).toHaveBeenCalledWith(
      "ws-1",
      expect.objectContaining({ status: "ACTIVE" }),
    );
  });

  it("shows an empty state when there are no active projects", async () => {
    listProjectsMock.mockResolvedValue({
      data: [],
      meta: { page: 1, per_page: 5, total: 0, total_pages: 0 },
    } satisfies CollectionEnvelope<Project>);

    renderWidget();

    expect(await screen.findByText("Nenhum projeto ativo")).toBeInTheDocument();
  });
});
