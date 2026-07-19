import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { WorkspaceInvitationsSettings } from "@/features/workspaces/components/WorkspaceInvitationsSettings";
import type { Invitation } from "@/features/workspaces/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { buildPaginationMeta } from "./mocks/fixtures";
import { server } from "./mocks/server";

function buildInvitation(overrides: Partial<Invitation>): Invitation {
  return {
    id: "inv-1",
    workspace_id: "ws-1",
    email: "new@example.com",
    role: "MEMBER",
    status: "PENDING",
    invited_by_id: "user-1",
    expires_at: "2026-02-01T00:00:00Z",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderSettings() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <WorkspaceInvitationsSettings workspaceId="ws-1" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkspaceInvitationsSettings", () => {
  it("fetches the first page of invitations", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/invitations`, () =>
        HttpResponse.json({
          data: [buildInvitation({ id: "inv-1" })],
          meta: buildPaginationMeta(1, 20, 1),
        }),
      ),
    );

    renderSettings();

    expect(await screen.findByText("new@example.com")).toBeInTheDocument();
  });

  it("shows pagination and moves to the next page on click", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/invitations`, ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get("page") ?? 1);
        if (page === 2) {
          return HttpResponse.json({
            data: [buildInvitation({ id: "inv-2", email: "page2@example.com" })],
            meta: buildPaginationMeta(2, 20, 40),
          });
        }
        return HttpResponse.json({
          data: [buildInvitation({ id: "inv-1" })],
          meta: buildPaginationMeta(1, 20, 40),
        });
      }),
    );
    const user = userEvent.setup();

    renderSettings();
    await screen.findByText("new@example.com");

    await user.click(screen.getByRole("button", { name: "Próxima página" }));

    expect(await screen.findByText("page2@example.com")).toBeInTheDocument();
  });
});
