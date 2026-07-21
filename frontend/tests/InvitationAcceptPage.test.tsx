import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { InvitationAcceptPage } from "@/pages/InvitationAcceptPage";
import { useAuthStore } from "@/shared/stores/authStore";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { demoMember, demoUser } from "./mocks/fixtures";
import { server } from "./mocks/server";

const TOKEN = "abc123";

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/invitations/${TOKEN}/accept`]}>
        <Routes>
          <Route path="/invitations/:token/accept" element={<InvitationAcceptPage />} />
          <Route path="/w/:slug/issues" element={<div>Issues da workspace</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function mockPreview(overrides: Partial<Record<string, unknown>> = {}) {
  server.use(
    http.get(`${API_BASE_URL}/invitations/${TOKEN}`, () =>
      HttpResponse.json({
        data: {
          email: "invitee@example.com",
          role: "MEMBER",
          status: "PENDING",
          workspace_name: "Acme",
          invited_by_name: "Ada Lovelace",
          ...overrides,
        },
      }),
    ),
  );
}

describe("InvitationAcceptPage", () => {
  afterEach(() => {
    useAuthStore.getState().clear();
  });

  it("shows an error for an invalid token", async () => {
    server.use(
      http.get(`${API_BASE_URL}/invitations/${TOKEN}`, () =>
        HttpResponse.json(
          { error: { code: "invitation_not_found", message: "Não encontrado." } },
          { status: 404 },
        ),
      ),
    );

    renderPage();

    expect(await screen.findByText("Este link de convite é inválido.")).toBeInTheDocument();
  });

  it("shows a message when the invitation was already accepted", async () => {
    mockPreview({ status: "ACCEPTED" });

    renderPage();

    expect(await screen.findByText("Convite já aceito")).toBeInTheDocument();
  });

  it("logged out: creates an account and accepts the invitation", async () => {
    mockPreview();
    server.use(
      http.post(`${API_BASE_URL}/invitations/${TOKEN}/accept`, () =>
        HttpResponse.json({ data: demoMember }),
      ),
      http.get(`${API_BASE_URL}/users/me`, () =>
        HttpResponse.json({
          data: {
            ...demoUser,
            workspaces: [
              { id: demoMember.workspace_id, name: "Acme", slug: "acme", role: "MEMBER" },
            ],
          },
        }),
      ),
    );
    const user = userEvent.setup();

    renderPage();
    await screen.findByText(/convidou você para/);

    await user.type(screen.getByLabelText("Nome completo"), "Nova Pessoa");
    await user.type(screen.getByLabelText("Senha"), "Senha-Forte123!");
    await user.click(screen.getByRole("button", { name: "Criar conta e entrar no workspace" }));

    expect(await screen.findByText("Issues da workspace")).toBeInTheDocument();
  });

  it("logged in with matching email: shows confirm/decline", async () => {
    mockPreview({ email: "ada@example.com" });
    useAuthStore.getState().setAuth("mock-token", demoUser);
    server.use(
      http.get(`${API_BASE_URL}/users/me`, () =>
        HttpResponse.json({ data: { ...demoUser, workspaces: [] } }),
      ),
    );

    renderPage();

    expect(await screen.findByRole("button", { name: "Aceitar como MEMBER" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Recusar" })).toBeInTheDocument();
  });

  it("logged in with a different email: shows a mismatch message", async () => {
    mockPreview({ email: "someone-else@example.com" });
    useAuthStore.getState().setAuth("mock-token", demoUser);
    server.use(
      http.get(`${API_BASE_URL}/users/me`, () =>
        HttpResponse.json({ data: { ...demoUser, workspaces: [] } }),
      ),
    );

    renderPage();

    expect(
      await screen.findByText(/Este convite foi emitido para someone-else@example.com/),
    ).toBeInTheDocument();
  });
});
