import { render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { App } from "@/app/App";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

describe("App", () => {
  it("renders the home page at the root route", async () => {
    // Sessão inexistente é um 401 de verdade do backend, não uma falha de rede —
    // `AuthBootstrap` só segue para `/login` quando distingue as duas (ADR-062).
    server.use(
      http.post(`${API_BASE_URL}/auth/refresh`, () => new HttpResponse(null, { status: 401 })),
    );

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Bem-vinda de volta" })).toBeInTheDocument();
  });
});
