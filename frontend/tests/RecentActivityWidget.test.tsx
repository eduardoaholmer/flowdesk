import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { RecentActivityWidget } from "@/features/dashboard/components/RecentActivityWidget";
import type { Notification } from "@/features/notifications/types";
import type { CollectionEnvelope } from "@/shared/lib/apiTypes";

const { listNotificationsMock } = vi.hoisted(() => ({ listNotificationsMock: vi.fn() }));

vi.mock("@/features/notifications/api", () => ({
  listNotifications: listNotificationsMock,
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}));

function renderWidget() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <RecentActivityWidget workspaceId="ws-1" workspaceSlug="acme" />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function buildNotification(overrides: Partial<Notification>): Notification {
  return {
    id: "notif-1",
    workspace_id: "ws-1",
    type: "MENTION",
    payload: { actor_name: "Ada Lovelace", issue_identifier: "FD-1" },
    read_at: null,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("RecentActivityWidget", () => {
  it("shows notifications belonging to the active workspace", async () => {
    listNotificationsMock.mockResolvedValue({
      data: [buildNotification({ id: "notif-1" })],
      meta: { page: 1, per_page: 10, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<Notification>);

    renderWidget();

    expect(await screen.findByText(/mencionou você em FD-1/)).toBeInTheDocument();
  });

  it("filters out notifications from other workspaces", async () => {
    listNotificationsMock.mockResolvedValue({
      data: [buildNotification({ id: "notif-other", workspace_id: "ws-2" })],
      meta: { page: 1, per_page: 10, total: 1, total_pages: 1 },
    } satisfies CollectionEnvelope<Notification>);

    renderWidget();

    expect(await screen.findByText("Nenhuma atividade recente")).toBeInTheDocument();
  });
});
