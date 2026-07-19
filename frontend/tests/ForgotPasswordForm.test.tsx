import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ForgotPasswordForm } from "@/features/auth/components/ForgotPasswordForm";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

describe("ForgotPasswordForm", () => {
  it("always shows a success message after submitting a valid e-mail", async () => {
    let receivedEmail: string | undefined;
    server.use(
      http.post(`${API_BASE_URL}/auth/password-reset/request`, async ({ request }) => {
        receivedEmail = ((await request.json()) as { email: string }).email;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ForgotPasswordForm />
      </MemoryRouter>,
    );

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(within(form).getByLabelText("E-mail"), "ada@example.com");
    await user.click(within(form).getByRole("button", { name: "Enviar link de redefinição" }));

    expect(await screen.findByText(/ada@example.com/)).toBeInTheDocument();
    expect(receivedEmail).toBe("ada@example.com");
  });

  it("keeps the form visible when the request fails", async () => {
    server.use(
      http.post(`${API_BASE_URL}/auth/password-reset/request`, () =>
        HttpResponse.json(
          {
            error: {
              code: "rate_limited",
              message: "Muitas tentativas. Tente novamente mais tarde.",
              details: null,
            },
          },
          { status: 429 },
        ),
      ),
    );
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ForgotPasswordForm />
      </MemoryRouter>,
    );

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(within(form).getByLabelText("E-mail"), "ada@example.com");
    await user.click(within(form).getByRole("button", { name: "Enviar link de redefinição" }));

    expect(await screen.findByLabelText("E-mail")).toBeInTheDocument();
  });
});
