import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";

import { AuthBootstrap } from "@/app/AuthBootstrap";
import { useAuthStore } from "@/shared/stores/authStore";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

afterEach(() => {
  useAuthStore.setState({ accessToken: null, user: null, bootstrapStatus: "initializing" });
});

describe("AuthBootstrap", () => {
  it("renders children once the silent refresh confirms there is no session (401)", async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/refresh`, () => new HttpResponse(null, { status: 401 })),
    );

    render(
      <AuthBootstrap>
        <div>Protected content</div>
      </AuthBootstrap>,
    );

    expect(await screen.findByText("Protected content")).toBeInTheDocument();
  });

  it("shows an explicit error state (not a silent logout) when the refresh call fails for an infra reason", async () => {
    server.use(http.post(`${API_BASE_URL}/auth/refresh`, () => HttpResponse.error()));

    render(
      <AuthBootstrap>
        <div>Protected content</div>
      </AuthBootstrap>,
    );

    expect(
      await screen.findByText(
        "Não foi possível carregar o FlowDesk. Verifique sua conexão ou tente novamente.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("retries the bootstrap and renders children once the retry succeeds", async () => {
    server.use(http.post(`${API_BASE_URL}/auth/refresh`, () => HttpResponse.error()));

    render(
      <AuthBootstrap>
        <div>Protected content</div>
      </AuthBootstrap>,
    );

    const retryButton = await screen.findByRole("button", { name: "Tentar novamente" });

    server.use(
      http.post(`${API_BASE_URL}/auth/refresh`, () => new HttpResponse(null, { status: 401 })),
    );
    retryButton.click();

    expect(await screen.findByText("Protected content")).toBeInTheDocument();
  });
});
