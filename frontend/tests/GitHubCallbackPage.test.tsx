import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GitHubCallbackPage } from "@/pages/GitHubCallbackPage";

function SettingsProbe() {
  const location = useLocation();
  return <div>Settings page {location.search}</div>;
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/integrations/github/callback" element={<GitHubCallbackPage />} />
        <Route path="/w/:workspaceSlug/settings" element={<SettingsProbe />} />
        <Route path="/" element={<div>Home page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  window.sessionStorage.clear();
  vi.restoreAllMocks();
});

describe("GitHubCallbackPage", () => {
  it("returns to the integrations tab of the workspace that started the connection", async () => {
    const toastSuccess = vi.spyOn(toast, "success");
    window.sessionStorage.setItem("flowdesk:github-connect-workspace", "acme");

    renderAt("/integrations/github/callback");

    expect(await screen.findByText("Settings page ?tab=integrations")).toBeInTheDocument();
    expect(toastSuccess).toHaveBeenCalledWith("GitHub conectado.");
    expect(window.sessionStorage.getItem("flowdesk:github-connect-workspace")).toBeNull();
  });

  it("shows the reason when the backend reports an error", async () => {
    const toastError = vi.spyOn(toast, "error");
    window.sessionStorage.setItem("flowdesk:github-connect-workspace", "acme");

    renderAt("/integrations/github/callback?error=github_installation_already_connected");

    expect(await screen.findByText("Settings page ?tab=integrations")).toBeInTheDocument();
    expect(toastError).toHaveBeenCalledWith(
      "Esta conta do GitHub já está conectada a outro workspace.",
    );
  });

  it("treats an installation waiting for owner approval as information, not failure", async () => {
    const toastInfo = vi.spyOn(toast, "info");
    const toastError = vi.spyOn(toast, "error");

    renderAt("/integrations/github/callback?error=github_installation_pending_approval");

    expect(await screen.findByText("Home page")).toBeInTheDocument();
    expect(toastInfo).toHaveBeenCalled();
    expect(toastError).not.toHaveBeenCalled();
  });
});
