import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ResetPasswordForm } from "@/features/auth/components/ResetPasswordForm";

const { confirmPasswordResetMock } = vi.hoisted(() => ({
  confirmPasswordResetMock: vi.fn(),
}));

vi.mock("@/features/auth/api", () => ({
  confirmPasswordReset: confirmPasswordResetMock,
}));

function renderForm() {
  return render(
    <MemoryRouter initialEntries={["/reset-password/tok123"]}>
      <Routes>
        <Route path="/reset-password/:token" element={<ResetPasswordForm token="tok123" />} />
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/forgot-password" element={<div>Forgot password page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ResetPasswordForm", () => {
  it("submits the new password and redirects to login on success", async () => {
    confirmPasswordResetMock.mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderForm();

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(within(form).getByLabelText("Nova senha"), "Str0ng!Passw0rd");
    await user.type(within(form).getByLabelText("Confirmar nova senha"), "Str0ng!Passw0rd");
    await user.click(within(form).getByRole("button", { name: "Redefinir senha" }));

    expect(await screen.findByText("Login page")).toBeInTheDocument();
    expect(confirmPasswordResetMock).toHaveBeenCalledWith({
      token: "tok123",
      new_password: "Str0ng!Passw0rd",
    });
  });

  it("shows a validation error when the passwords do not match", async () => {
    const user = userEvent.setup();

    renderForm();

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(within(form).getByLabelText("Nova senha"), "Str0ng!Passw0rd");
    await user.type(within(form).getByLabelText("Confirmar nova senha"), "Different1!");
    await user.click(within(form).getByRole("button", { name: "Redefinir senha" }));

    expect(await screen.findByText("As senhas não coincidem.")).toBeInTheDocument();
    expect(confirmPasswordResetMock).not.toHaveBeenCalled();
  });

  it("offers a link to request a new token when the token is invalid or expired", async () => {
    confirmPasswordResetMock.mockRejectedValue({ isAxiosError: true, response: { status: 401 } });
    const user = userEvent.setup();

    renderForm();

    const form = document.querySelector("form");
    if (!form) throw new Error("expected a form element");

    await user.type(within(form).getByLabelText("Nova senha"), "Str0ng!Passw0rd");
    await user.type(within(form).getByLabelText("Confirmar nova senha"), "Str0ng!Passw0rd");
    await user.click(within(form).getByRole("button", { name: "Redefinir senha" }));

    expect(await screen.findByText("Solicitar um novo link")).toBeInTheDocument();
  });
});
