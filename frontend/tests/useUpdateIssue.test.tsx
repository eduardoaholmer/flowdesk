import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { useUpdateIssue } from "@/features/issues/hooks";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { demoIssue } from "./mocks/fixtures";
import { server } from "./mocks/server";

const workspaceId = "workspace-1";

function renderUpdateIssue() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  return renderHook(() => useUpdateIssue(workspaceId, demoIssue.id), { wrapper });
}

describe("useUpdateIssue", () => {
  it("sends due_date as an explicit null when clearing the field, not an omitted key", async () => {
    let receivedBody: unknown;
    server.use(
      http.patch(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId`, async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: { ...demoIssue, due_date: null } });
      }),
    );
    const { result } = renderUpdateIssue();

    result.current.mutate({ due_date: null });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receivedBody).toHaveProperty("due_date", null);
  });

  it("omits due_date entirely from the request body when the field isn't touched", async () => {
    let receivedBody: unknown;
    server.use(
      http.patch(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId`, async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: demoIssue });
      }),
    );
    const { result } = renderUpdateIssue();

    result.current.mutate({ title: "Novo título" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receivedBody).not.toHaveProperty("due_date");
  });
});
