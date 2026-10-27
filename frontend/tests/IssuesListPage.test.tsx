import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { IssuesListPage } from "@/features/issues/components/IssuesListPage";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { buildPaginationMeta, demoIssue } from "./mocks/fixtures";
import { server } from "./mocks/server";

const issueA = { ...demoIssue, id: "issue-a", identifier: "FLW-1", title: "Primeira issue" };
const issueB = { ...demoIssue, id: "issue-b", identifier: "FLW-2", title: "Segunda issue" };

function mockIssueDetailDependencies() {
  server.use(
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues`, ({ request }) => {
      const url = new URL(request.url);
      const parentId = url.searchParams.get("parent_id");
      // Sub-issues query (parent_id set) sempre vazia neste teste — só o
      // painel principal precisa das duas issues de topo.
      const data = parentId ? [] : [issueA, issueB];
      return HttpResponse.json({ data, meta: buildPaginationMeta(1, 20, data.length) });
    }),
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId`, ({ params }) => {
      const issue = params.issueId === issueA.id ? issueA : issueB;
      return HttpResponse.json({ data: issue });
    }),
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/attachments`, () =>
      HttpResponse.json({ data: [] }),
    ),
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/comments`, () =>
      HttpResponse.json({ data: [], meta: buildPaginationMeta(1, 20, 0) }),
    ),
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/activity`, () =>
      HttpResponse.json({ data: [] }),
    ),
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/labels`, () =>
      HttpResponse.json({ data: [] }),
    ),
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/labels`, () =>
      HttpResponse.json({ data: [] }),
    ),
  );
}

function renderIssuesListPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/w/acme/issues"]}>
        <IssuesListPage workspaceId="ws-1" workspaceSlug="acme" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("IssuesListPage split view", () => {
  it("opens the side panel with the clicked issue's detail, keeping the list mounted", async () => {
    mockIssueDetailDependencies();
    const user = userEvent.setup();
    renderIssuesListPage();

    await user.click(await screen.findByRole("link", { name: "Primeira issue" }));

    expect(await screen.findByRole("button", { name: "Fechar painel" })).toBeInTheDocument();
    expect(screen.getAllByText("Primeira issue").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Segunda issue" })).toBeInTheDocument();
  });

  it("closes the panel when the close button is clicked", async () => {
    mockIssueDetailDependencies();
    const user = userEvent.setup();
    renderIssuesListPage();

    await user.click(await screen.findByRole("link", { name: "Primeira issue" }));
    await screen.findByRole("button", { name: "Fechar painel" });

    await user.click(screen.getByRole("button", { name: "Fechar painel" }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Fechar painel" })).not.toBeInTheDocument(),
    );
  });

  it("navigates to the next issue in the panel via the next button", async () => {
    mockIssueDetailDependencies();
    const user = userEvent.setup();
    renderIssuesListPage();

    await user.click(await screen.findByRole("link", { name: "Primeira issue" }));
    await screen.findByRole("button", { name: "Fechar painel" });

    await user.click(screen.getByRole("button", { name: "Próxima issue" }));

    await waitFor(() => expect(screen.getAllByText("Segunda issue").length).toBeGreaterThan(1));
  });
});
