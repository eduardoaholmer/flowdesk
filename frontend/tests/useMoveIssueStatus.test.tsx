import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { useMoveIssueStatus } from "@/features/issues/hooks";
import type { CollectionEnvelope } from "@/shared/lib/apiTypes";
import type { Issue } from "@/features/issues/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { buildPaginationMeta, demoIssue } from "./mocks/fixtures";
import { server } from "./mocks/server";

const workspaceId = "workspace-1";
const listParams = { page: 1, per_page: 100 } as const;
const listKey = ["workspaces", workspaceId, "issues", listParams] as const;

function renderMoveIssueStatus(initialIssues: Issue[]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData<CollectionEnvelope<Issue>>(listKey, {
    data: initialIssues,
    meta: buildPaginationMeta(1, 100, initialIssues.length),
  });

  function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  const { result } = renderHook(() => useMoveIssueStatus(workspaceId, listParams), { wrapper });
  return { result, queryClient };
}

describe("useMoveIssueStatus", () => {
  it("applies the new status to the list cache optimistically, before the request settles", async () => {
    server.use(
      http.patch(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 20));
        return HttpResponse.json({ data: { ...demoIssue, status: "IN_PROGRESS" } });
      }),
    );
    const { result, queryClient } = renderMoveIssueStatus([demoIssue]);

    result.current.mutate({ issueId: demoIssue.id, status: "IN_PROGRESS" });

    await waitFor(() => {
      const cached = queryClient.getQueryData<CollectionEnvelope<Issue>>(listKey);
      expect(cached?.data[0]?.status).toBe("IN_PROGRESS");
    });
  });

  it("rolls back the optimistic move if the request fails", async () => {
    server.use(
      http.patch(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId`, () =>
        HttpResponse.json(
          { error: { code: "issue_not_found", message: "Issue não encontrada.", details: null } },
          { status: 404 },
        ),
      ),
    );
    const { result, queryClient } = renderMoveIssueStatus([demoIssue]);

    result.current.mutate({ issueId: demoIssue.id, status: "IN_PROGRESS" });

    await waitFor(() => expect(result.current.isError).toBe(true));

    const cached = queryClient.getQueryData<CollectionEnvelope<Issue>>(listKey);
    expect(cached?.data[0]?.status).toBe(demoIssue.status);
  });
});
