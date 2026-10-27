import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { CreateIssueDialog } from "@/features/issues/components/CreateIssueDialog";
import { IssueLabelPicker } from "@/features/labels/components/IssueLabelPicker";
import type { Label } from "@/features/labels/types";
import { useUiStore } from "@/shared/stores/uiStore";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { demoIssue } from "./mocks/fixtures";
import { server } from "./mocks/server";

const workspaceId = "workspace-1";

const bugLabel: Label = {
  id: "label-bug",
  workspace_id: workspaceId,
  name: "bug",
  color: "#EF4444",
  description: null,
  issue_count: 0,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderWithQueryClient(ui: ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

function mockLabels(existing: Label[]) {
  const createdBodies: unknown[] = [];
  server.use(
    http.get(`${API_BASE_URL}/workspaces/:workspaceId/labels`, () =>
      HttpResponse.json({ data: existing }),
    ),
    http.post(`${API_BASE_URL}/workspaces/:workspaceId/labels`, async ({ request }) => {
      const body = (await request.json()) as { name: string; color: string };
      createdBodies.push(body);
      return HttpResponse.json(
        { data: { ...bugLabel, id: "label-new", name: body.name, color: body.color } },
        { status: 201 },
      );
    }),
  );
  return createdBodies;
}

describe("IssueLabelPicker", () => {
  it("creates a label from the search term and applies it to the issue", async () => {
    const createdBodies = mockLabels([bugLabel]);
    const appliedLabelIds: string[] = [];
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/labels`, () =>
        HttpResponse.json({ data: [] }),
      ),
      http.post(
        `${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/labels`,
        async ({ request }) => {
          const body = (await request.json()) as { label_id: string };
          appliedLabelIds.push(body.label_id);
          return HttpResponse.json({ data: bugLabel }, { status: 201 });
        },
      ),
    );
    const user = userEvent.setup();
    renderWithQueryClient(<IssueLabelPicker workspaceId={workspaceId} issueId={demoIssue.id} />);

    await user.click(screen.getByRole("button", { name: "Gerenciar labels" }));
    await user.type(await screen.findByPlaceholderText("Buscar ou criar label…"), "frontend");
    await user.click(await screen.findByText("Criar label “frontend”"));

    await waitFor(() => expect(appliedLabelIds).toEqual(["label-new"]));
    expect(createdBodies).toEqual([{ name: "frontend", color: expect.any(String) }]);
  });

  it("does not offer to create a label whose name already exists", async () => {
    mockLabels([bugLabel]);
    server.use(
      http.get(`${API_BASE_URL}/workspaces/:workspaceId/issues/:issueId/labels`, () =>
        HttpResponse.json({ data: [] }),
      ),
    );
    const user = userEvent.setup();
    renderWithQueryClient(<IssueLabelPicker workspaceId={workspaceId} issueId={demoIssue.id} />);

    await user.click(screen.getByRole("button", { name: "Gerenciar labels" }));
    await user.type(await screen.findByPlaceholderText("Buscar ou criar label…"), "BUG");

    expect(await screen.findByText("bug")).toBeInTheDocument();
    expect(screen.queryByText(/Criar label/)).not.toBeInTheDocument();
  });
});

describe("CreateIssueDialog", () => {
  it("sends labels created and selected in the dialog as label_ids", async () => {
    mockLabels([bugLabel]);
    let createIssueBody: unknown;
    server.use(
      http.post(`${API_BASE_URL}/workspaces/:workspaceId/issues`, async ({ request }) => {
        createIssueBody = await request.json();
        return HttpResponse.json({ data: demoIssue }, { status: 201 });
      }),
    );
    useUiStore.setState({ isCreateIssueOpen: true, createIssueParentId: null });
    const user = userEvent.setup();
    renderWithQueryClient(<CreateIssueDialog workspaceId={workspaceId} />);

    await user.type(await screen.findByLabelText("Título"), "Nova tela de login");
    await user.click(screen.getByRole("button", { name: "Adicionar labels" }));
    await user.click(await screen.findByText("bug"));
    await user.type(screen.getByPlaceholderText("Buscar ou criar label…"), "frontend");
    await user.click(await screen.findByText("Criar label “frontend”"));
    await user.keyboard("{Escape}");
    await user.click(screen.getByRole("button", { name: "Criar issue" }));

    await waitFor(() =>
      expect(createIssueBody).toMatchObject({
        title: "Nova tela de login",
        label_ids: ["label-bug", "label-new"],
      }),
    );
  });
});
