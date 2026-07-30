import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { PermissionsSettings } from "@/features/permissions/components/PermissionsSettings";

function renderSettings() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <PermissionsSettings workspaceId="ws-1" />
    </QueryClientProvider>,
  );
}

describe("PermissionsSettings", () => {
  it("renders the matrix with one switch per role for each permission", async () => {
    renderSettings();

    await screen.findByText("Criar issue");
    expect(screen.getByRole("switch", { name: /criar issue — admin/i })).toBeChecked();
    expect(screen.getByRole("switch", { name: /criar issue — membro/i })).toBeChecked();
    expect(screen.getByRole("switch", { name: /criar issue — convidado/i })).not.toBeChecked();
  });

  it("toggling a switch grants the permission and marks it as customized", async () => {
    const user = userEvent.setup();
    renderSettings();

    const guestSwitch = await screen.findByRole("switch", { name: /criar issue — convidado/i });
    await user.click(guestSwitch);

    await waitFor(() => expect(guestSwitch).toBeChecked());
    expect(screen.getAllByText("Customizado").length).toBeGreaterThan(0);
  });
});
