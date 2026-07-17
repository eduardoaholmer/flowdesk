import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceMembersSettings } from "@/features/workspaces/components/WorkspaceMembersSettings";
import type { WorkspaceMember } from "@/features/workspaces/types";
import type { UserProfile } from "@/features/auth/types";
import type { CollectionEnvelope } from "@/shared/lib/apiTypes";

const { listWorkspaceMembersPageMock } = vi.hoisted(() => ({
  listWorkspaceMembersPageMock: vi.fn(),
}));

vi.mock("@/features/workspaces/api", () => ({
  listWorkspaceMembersPage: listWorkspaceMembersPageMock,
}));

const profile: UserProfile = {
  id: "user-1",
  name: "Ada Lovelace",
  email: "ada@example.com",
  avatar_url: null,
  created_at: "2026-01-01T00:00:00Z",
  workspaces: [{ id: "ws-1", name: "Acme", slug: "acme", role: "OWNER" }],
};

vi.mock("@/shared/hooks/useCurrentUser", () => ({
  useCurrentUser: () => ({ data: profile, isLoading: false }),
}));

function buildMember(overrides: Partial<WorkspaceMember>): WorkspaceMember {
  return {
    id: "member-1",
    workspace_id: "ws-1",
    role: "MEMBER",
    status: "ACTIVE",
    joined_at: "2026-01-01T00:00:00Z",
    user: { id: "user-1", name: "Ada Lovelace", email: "ada@example.com", avatar_url: null },
    ...overrides,
  };
}

function renderSettings() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <WorkspaceMembersSettings workspaceId="ws-1" canManage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkspaceMembersSettings", () => {
  it("fetches the first page without a role filter by default", async () => {
    listWorkspaceMembersPageMock.mockResolvedValue({
      data: [buildMember({ id: "member-1" })],
      meta: { page: 1, per_page: 20, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<WorkspaceMember>);

    renderSettings();

    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
    expect(listWorkspaceMembersPageMock).toHaveBeenCalledWith("ws-1", {
      page: 1,
      per_page: 20,
      role: undefined,
    });
  });

  it("re-fetches with the selected role and resets to page 1", async () => {
    listWorkspaceMembersPageMock.mockResolvedValue({
      data: [buildMember({ id: "member-1" })],
      meta: { page: 1, per_page: 20, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<WorkspaceMember>);
    const user = userEvent.setup();

    renderSettings();
    await screen.findByText("Ada Lovelace");

    await user.click(screen.getByRole("combobox"));
    await user.click(await screen.findByRole("option", { name: "ADMIN" }));

    await waitFor(() => {
      expect(listWorkspaceMembersPageMock).toHaveBeenLastCalledWith("ws-1", {
        page: 1,
        per_page: 20,
        role: "ADMIN",
      });
    });
  });

  it("shows pagination and moves to the next page on click", async () => {
    listWorkspaceMembersPageMock.mockResolvedValue({
      data: [buildMember({ id: "member-1" })],
      meta: { page: 1, per_page: 20, total: 40, total_pages: 2 },
    } satisfies CollectionEnvelope<WorkspaceMember>);
    const user = userEvent.setup();

    renderSettings();
    await screen.findByText("Ada Lovelace");

    await user.click(screen.getByRole("button", { name: "Próxima página" }));

    expect(listWorkspaceMembersPageMock).toHaveBeenLastCalledWith("ws-1", {
      page: 2,
      per_page: 20,
      role: undefined,
    });
  });
});
