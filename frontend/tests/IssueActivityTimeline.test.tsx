import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { IssueActivityTimeline } from "@/features/issues/components/IssueActivityTimeline";
import type { IssueActivityLogEntry } from "@/features/issues/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

function entry(overrides: Partial<IssueActivityLogEntry>): IssueActivityLogEntry {
  return {
    id: "a-1",
    issue_id: "issue-1",
    actor_id: "user-1",
    actor_source: "USER",
    action: "issue.status_changed",
    field: "status",
    old_value: "In Review",
    new_value: "Done",
    created_at: "2026-10-27T12:00:00Z",
    ...overrides,
  };
}

describe("IssueActivityTimeline", () => {
  it("marks changes made by the GitHub automation", async () => {
    server.use(
      http.get(`${API_BASE_URL}/workspaces/ws-1/issues/issue-1/activity`, () =>
        HttpResponse.json({
          data: [
            entry({ id: "a-1", actor_id: null, actor_source: "GITHUB" }),
            entry({ id: "a-2", old_value: "Todo", new_value: "In Review" }),
          ],
        }),
      ),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <IssueActivityTimeline workspaceId="ws-1" issueId="issue-1" />
      </QueryClientProvider>,
    );

    const items = await screen.findAllByRole("listitem");
    expect(items[0]).toHaveTextContent("via GitHub");
    expect(items[1]).not.toHaveTextContent("via GitHub");
  });
});
