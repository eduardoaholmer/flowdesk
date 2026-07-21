import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { MyIssuesWidget } from "@/features/dashboard/components/MyIssuesWidget";
import type { CollectionEnvelope } from "@/shared/lib/apiTypes";
import type { Issue } from "@/features/issues/types";

const { listIssuesMock } = vi.hoisted(() => ({ listIssuesMock: vi.fn() }));

vi.mock("@/features/issues/api", () => ({
  listIssues: listIssuesMock,
}));

function renderWidget() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <MyIssuesWidget workspaceId="ws-1" workspaceSlug="acme" userId="user-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const baseIssue: Issue = {
  id: "issue-1",
  workspace_id: "ws-1",
  project_id: null,
  identifier: "FD-1",
  number: 1,
  title: "Corrigir tela de login",
  description: null,
  status: "TODO",
  priority: "HIGH",
  assignee_id: "user-1",
  creator_id: "user-1",
  estimate: null,
  due_date: null,
  version: 1,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("MyIssuesWidget", () => {
  it("shows issues assigned to the current user", async () => {
    listIssuesMock.mockResolvedValue({
      data: [baseIssue],
      meta: { page: 1, per_page: 5, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<Issue>);

    renderWidget();

    expect(await screen.findByText("Corrigir tela de login")).toBeInTheDocument();
    expect(listIssuesMock).toHaveBeenCalledWith(
      "ws-1",
      expect.objectContaining({ assignee_id: "user-1" }),
    );
  });

  it("shows an empty state when the user has no assigned issues", async () => {
    listIssuesMock.mockResolvedValue({
      data: [],
      meta: { page: 1, per_page: 20, total: 0, total_pages: 0 },
    } satisfies CollectionEnvelope<Issue>);

    renderWidget();

    expect(await screen.findByText("Nada atribuído a você")).toBeInTheDocument();
  });
});
