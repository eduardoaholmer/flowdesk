import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/features/auth/components/LoginForm";
import { useAuthStore } from "@/shared/stores/authStore";

vi.mock("@/features/auth/api", () => ({
  login: vi.fn(async () => ({
    access_token: "token",
    user: {
      id: "1",
      name: "Ada Lovelace",
      email: "ada@example.com",
      avatar_url: null,
      created_at: "2026-01-01T00:00:00Z",
    },
  })),
  register: vi.fn(),
}));

afterEach(() => {
  useAuthStore.getState().clear();
});

describe("LoginForm", () => {
  it("redirects to redirectTo after login instead of always going home", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginForm redirectTo="/invitations/abc123/accept" />} />
          <Route path="/invitations/:token/accept" element={<div>Invitation page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(screen.getByLabelText("E-mail"), "ada@example.com");
    await user.type(screen.getByLabelText("Senha"), "correct-password");
    await user.click(within(form).getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("Invitation page")).toBeInTheDocument();
  });

  it("falls back to home when no redirectTo is provided", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/" element={<div>Home page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(screen.getByLabelText("E-mail"), "ada@example.com");
    await user.type(screen.getByLabelText("Senha"), "correct-password");
    await user.click(within(form).getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("Home page")).toBeInTheDocument();
  });
});
