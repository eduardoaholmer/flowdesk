import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { CommandPalette } from "@/shared/components/command-palette/CommandPalette";
import type { UserProfile } from "@/features/auth/types";
import { useUiStore } from "@/shared/stores/uiStore";

const { listIssuesMock } = vi.hoisted(() => ({ listIssuesMock: vi.fn() }));
const { listProjectsMock } = vi.hoisted(() => ({ listProjectsMock: vi.fn() }));

vi.mock("@/features/issues/api", () => ({ listIssues: listIssuesMock }));
vi.mock("@/features/projects/api", () => ({ listProjects: listProjectsMock }));
vi.mock("@/features/auth/api", () => ({ logout: vi.fn() }));

vi.mock("@/features/workspaces/useWorkspace", () => ({
  useWorkspace: () => ({
    workspace: { id: "ws-1", slug: "acme", name: "Acme" },
    isLoading: false,
    isError: false,
    notFound: false,
  }),
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

function renderPalette() {
  useUiStore.setState({ isCommandPaletteOpen: true });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CommandPalette />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function deferred<T = unknown>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

describe("CommandPalette search", () => {
  it("shows a loading indicator while the search is in flight, then the results", async () => {
    const issues = deferred();
    listIssuesMock.mockReturnValue(issues.promise);
    const projects = deferred();
    listProjectsMock.mockReturnValue(projects.promise);
    const user = userEvent.setup();

    renderPalette();
    await user.type(screen.getByPlaceholderText(/Digite um comando/), "auth");

    expect(await screen.findByText("Buscando…")).toBeInTheDocument();

    issues.resolve({
      data: [{ id: "issue-1", identifier: "FD-1", title: "Corrigir auth" }],
      meta: { page: 1, per_page: 5, total: 1, total_pages: 1 },
    });
    projects.resolve({ data: [], meta: { page: 1, per_page: 5, total: 0, total_pages: 0 } });

    expect(await screen.findByText("Corrigir auth")).toBeInTheDocument();
    expect(screen.queryByText("Buscando…")).not.toBeInTheDocument();
  });

  it("shows an error state with a retry action when the search fails", async () => {
    listIssuesMock.mockRejectedValue(new Error("network error"));
    listProjectsMock.mockResolvedValue({
      data: [],
      meta: { page: 1, per_page: 5, total: 0, total_pages: 0 },
    });
    const user = userEvent.setup();

    renderPalette();
    await user.type(screen.getByPlaceholderText(/Digite um comando/), "auth");

    expect(await screen.findByText("Não foi possível buscar issues/projetos.")).toBeInTheDocument();

    listIssuesMock.mockResolvedValue({
      data: [{ id: "issue-1", identifier: "FD-1", title: "Corrigir auth" }],
      meta: { page: 1, per_page: 5, total: 1, total_pages: 1 },
    });
    await user.click(screen.getByRole("button", { name: "Tentar novamente" }));

    expect(await screen.findByText("Corrigir auth")).toBeInTheDocument();
  });
});
