import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ForgotPasswordForm } from "@/features/auth/components/ForgotPasswordForm";

const { requestPasswordResetMock } = vi.hoisted(() => ({
  requestPasswordResetMock: vi.fn(),
}));

vi.mock("@/features/auth/api", () => ({
  requestPasswordReset: requestPasswordResetMock,
}));

describe("ForgotPasswordForm", () => {
  it("always shows a success message after submitting a valid e-mail", async () => {
    requestPasswordResetMock.mockResolvedValue(undefined);
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
    expect(requestPasswordResetMock).toHaveBeenCalledWith("ada@example.com");
  });

  it("keeps the form visible when the request fails", async () => {
    requestPasswordResetMock.mockRejectedValue(new Error("network error"));
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
