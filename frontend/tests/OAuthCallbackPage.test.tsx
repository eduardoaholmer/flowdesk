import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { OAuthCallbackPage } from "@/pages/OAuthCallbackPage";
import { useAuthStore } from "@/shared/stores/authStore";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

afterEach(() => {
  useAuthStore.getState().clear();
});

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/" element={<div>Home page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OAuthCallbackPage", () => {
  it("refreshes the access token and redirects home on success", async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/refresh`, () =>
        HttpResponse.json({ data: { access_token: "mock-refreshed-access-token" } }),
      ),
    );

    renderAt("/oauth/callback");

    expect(await screen.findByText("Home page")).toBeInTheDocument();
    expect(useAuthStore.getState().accessToken).toBe("mock-refreshed-access-token");
  });

  it("redirects to login with an error toast when the provider reports a failure", async () => {
    renderAt("/oauth/callback?error=oauth_authentication_failed");

    expect(await screen.findByText("Login page")).toBeInTheDocument();
    expect(useAuthStore.getState().accessToken).toBeNull();
  });

  it("redirects to login when the silent refresh itself fails", async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/refresh`, () => new HttpResponse(null, { status: 401 })),
    );

    renderAt("/oauth/callback");

    expect(await screen.findByText("Login page")).toBeInTheDocument();
  });
});
