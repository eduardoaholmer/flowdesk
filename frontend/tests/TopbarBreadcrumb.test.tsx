import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Topbar } from "@/shared/components/layout/Topbar";
import type { UserProfile } from "@/features/auth/types";

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

vi.mock("@/features/notifications/hooks", () => ({
  useRecentNotifications: () => ({ data: undefined, isLoading: false }),
  useUnreadNotificationsCount: () => ({ data: 0 }),
  useMarkNotificationRead: () => ({ mutate: vi.fn() }),
  useMarkAllNotificationsRead: () => ({ mutate: vi.fn() }),
}));

const { useIssueMock } = vi.hoisted(() => ({ useIssueMock: vi.fn() }));
vi.mock("@/features/issues/hooks", () => ({ useIssue: useIssueMock }));

const { useProjectMock } = vi.hoisted(() => ({ useProjectMock: vi.fn() }));
vi.mock("@/features/projects/hooks", () => ({ useProject: useProjectMock }));

function renderTopbarAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/w/:workspaceSlug/*" element={<Topbar />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Topbar breadcrumb", () => {
  it("shows the issue identifier instead of a literal 'Detalhe' on an issue detail page", async () => {
    useIssueMock.mockReturnValue({ data: { identifier: "FD-42" } });
    useProjectMock.mockReturnValue({ data: undefined });

    renderTopbarAt("/w/acme/issues/issue-123");

    expect(await screen.findByText("FD-42")).toBeInTheDocument();
    expect(screen.queryByText("Detalhe")).not.toBeInTheDocument();
    expect(useIssueMock).toHaveBeenCalledWith("ws-1", "issue-123");
  });

  it("shows the project name instead of a literal 'Detalhe' on a project detail page", async () => {
    useIssueMock.mockReturnValue({ data: undefined });
    useProjectMock.mockReturnValue({ data: { name: "Ring Gate" } });

    renderTopbarAt("/w/acme/projects/project-9");

    expect(await screen.findByText("Ring Gate")).toBeInTheDocument();
    expect(screen.queryByText("Detalhe")).not.toBeInTheDocument();
    expect(useProjectMock).toHaveBeenCalledWith("ws-1", "project-9");
  });

  it("shows a loading placeholder while the detail is still resolving", async () => {
    useIssueMock.mockReturnValue({ data: undefined });
    useProjectMock.mockReturnValue({ data: undefined });

    renderTopbarAt("/w/acme/issues/issue-123");

    expect(await screen.findByText("…")).toBeInTheDocument();
  });
});
