import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GitHubIntegrationSettings } from "@/features/github/components/GitHubIntegrationSettings";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

const INTEGRATION_URL = `${API_BASE_URL}/workspaces/ws-1/integrations/github`;

function renderSettings() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <GitHubIntegrationSettings workspaceId="ws-1" workspaceSlug="acme" />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  window.sessionStorage.clear();
});

describe("GitHubIntegrationSettings", () => {
  it("lists connected accounts with who connected them", async () => {
    renderSettings();

    expect(await screen.findByText("acme-org")).toBeInTheDocument();
    expect(screen.getByText("Organização")).toBeInTheDocument();
    expect(await screen.findByText(/Conectada por Ada Lovelace/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Conectar GitHub/ })).toBeInTheDocument();
  });

  it("explains the integration is unavailable when the app is not configured", async () => {
    server.use(
      http.get(INTEGRATION_URL, () =>
        HttpResponse.json({ data: { configured: false, installations: [] } }),
      ),
    );

    renderSettings();

    expect(await screen.findByText("Integração indisponível")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Conectar GitHub/ })).not.toBeInTheDocument();
  });

  it("sends the browser to the GitHub install page and remembers the workspace", async () => {
    const user = userEvent.setup();
    const originalLocation = window.location;
    const assign = vi.fn();
    // `assign` de verdade navegaria o jsdom para fora da página de teste.
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...originalLocation, assign },
    });

    try {
      renderSettings();
      await user.click(await screen.findByRole("button", { name: /Conectar GitHub/ }));

      await waitFor(() =>
        expect(assign).toHaveBeenCalledWith(
          "https://github.com/apps/flowdesk/installations/new?state=mock-state",
        ),
      );
      expect(window.sessionStorage.getItem("flowdesk:github-connect-workspace")).toBe("acme");
    } finally {
      Object.defineProperty(window, "location", { configurable: true, value: originalLocation });
    }
  });

  it("disconnects an account after confirmation", async () => {
    const user = userEvent.setup();
    let deletedId: string | undefined;
    server.use(
      http.delete(`${INTEGRATION_URL}/installations/:installationId`, ({ params }) => {
        deletedId = params.installationId as string;
        server.use(
          http.get(INTEGRATION_URL, () =>
            HttpResponse.json({ data: { configured: true, installations: [] } }),
          ),
        );
        return new HttpResponse(null, { status: 204 });
      }),
    );

    renderSettings();
    await user.click(await screen.findByRole("button", { name: "Desconectar" }));
    await user.click(
      within(screen.getByRole("alertdialog")).getByRole("button", { name: "Desconectar" }),
    );

    expect(await screen.findByText("Nenhuma conta conectada")).toBeInTheDocument();
    expect(deletedId).toBe("gh-installation-1");
  });
});
