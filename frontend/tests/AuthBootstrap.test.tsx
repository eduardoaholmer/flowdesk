import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { AuthBootstrap } from "@/app/AuthBootstrap";
import { useAuthStore } from "@/shared/stores/authStore";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

function setSessionCookie() {
  document.cookie = "csrf_token=test-csrf-token; path=/";
}

function clearCookies() {
  document.cookie = "csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
}

// `beforeEach` (não `afterEach`) porque o `cleanup()` global (`tests/setup.ts`)
// já garantiu, antes deste hook, que o componente do teste anterior está
// desmontado — resetar aqui evita reagir a um componente ainda montado (efeito
// colateral de hooks `afterEach` rodarem em ordem LIFO, antes do `cleanup()`).
beforeEach(() => {
  useAuthStore.setState({ accessToken: null, user: null, bootstrapStatus: "initializing" });
  clearCookies();
});

describe("AuthBootstrap", () => {
  it("renders children once the silent refresh confirms there is no session (401)", async () => {
    setSessionCookie();
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
    setSessionCookie();
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
    setSessionCookie();
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

  it("skips the refresh call and renders children immediately when there is no session cookie", async () => {
    let refreshCalled = false;
    server.use(
      http.post(`${API_BASE_URL}/auth/refresh`, () => {
        refreshCalled = true;
        return new HttpResponse(null, { status: 401 });
      }),
    );

    render(
      <AuthBootstrap>
        <div>Protected content</div>
      </AuthBootstrap>,
    );

    expect(await screen.findByText("Protected content")).toBeInTheDocument();
    expect(refreshCalled).toBe(false);
  });
});
