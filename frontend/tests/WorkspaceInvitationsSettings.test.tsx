import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceInvitationsSettings } from "@/features/workspaces/components/WorkspaceInvitationsSettings";
import type { Invitation } from "@/features/workspaces/types";
import type { CollectionEnvelope } from "@/shared/lib/apiTypes";

const { listInvitationsMock } = vi.hoisted(() => ({ listInvitationsMock: vi.fn() }));

vi.mock("@/features/workspaces/api", () => ({
  listInvitations: listInvitationsMock,
}));

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
    listInvitationsMock.mockResolvedValue({
      data: [buildInvitation({ id: "inv-1" })],
      meta: { page: 1, per_page: 20, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<Invitation>);

    renderSettings();

    expect(await screen.findByText("new@example.com")).toBeInTheDocument();
    expect(listInvitationsMock).toHaveBeenCalledWith("ws-1", { page: 1, per_page: 20 });
  });

  it("shows pagination and moves to the next page on click", async () => {
    listInvitationsMock.mockResolvedValue({
      data: [buildInvitation({ id: "inv-1" })],
      meta: { page: 1, per_page: 20, total: 40, total_pages: 2 },
    } satisfies CollectionEnvelope<Invitation>);
    const user = userEvent.setup();

    renderSettings();
    await screen.findByText("new@example.com");

    await user.click(screen.getByRole("button", { name: "Próxima página" }));

    expect(listInvitationsMock).toHaveBeenLastCalledWith("ws-1", { page: 2, per_page: 20 });
  });
});
