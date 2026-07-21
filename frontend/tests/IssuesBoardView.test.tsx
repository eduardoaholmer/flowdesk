import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { IssuesBoardView } from "@/features/issues/components/IssuesBoardView";
import type { Issue } from "@/features/issues/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { buildPaginationMeta, demoIssue } from "./mocks/fixtures";
import { server } from "./mocks/server";

function renderBoard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <IssuesBoardView workspaceId="ws-1" workspaceSlug="acme" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function mockIssues(issues: Issue[]) {
  server.use(
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues`, () =>
      HttpResponse.json({ data: issues, meta: buildPaginationMeta(1, 100, issues.length) }),
    ),
  );
}

describe("IssuesBoardView", () => {
  it("groups issues into the column matching their status", async () => {
    mockIssues([
      { ...demoIssue, id: "issue-todo", identifier: "FLW-1", title: "A fazer", status: "TODO" },
      {
        ...demoIssue,
        id: "issue-done",
        identifier: "FLW-2",
        title: "Concluída",
        status: "DONE",
      },
    ]);

    renderBoard();

    const todoColumn = (await screen.findByText("A fazer")).closest('[data-slot="board-column"]');
    const doneColumn = screen.getByText("Concluída").closest('[data-slot="board-column"]');

    expect(todoColumn).not.toBeNull();
    expect(doneColumn).not.toBeNull();
    expect(within(todoColumn as HTMLElement).getByText("A fazer")).toBeInTheDocument();
    expect(within(todoColumn as HTMLElement).queryByText("Concluída")).not.toBeInTheDocument();
    expect(within(doneColumn as HTMLElement).getByText("Concluída")).toBeInTheDocument();
  });

  it("shows an empty-column message for statuses with no issues", async () => {
    mockIssues([{ ...demoIssue, status: "TODO" }]);

    renderBoard();

    await screen.findByText(demoIssue.title);
    const backlogColumn = screen
      .getByText("Backlog")
      .closest('[data-slot="board-column"]') as HTMLElement;

    expect(within(backlogColumn).getByText("Solte um cartão aqui")).toBeInTheDocument();
  });
});
