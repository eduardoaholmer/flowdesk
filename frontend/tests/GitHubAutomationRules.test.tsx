import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { GitHubAutomationRules } from "@/features/github/components/GitHubAutomationRules";
import type { GitHubStatusAutomation } from "@/features/github/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { demoGitHubAutomations } from "./mocks/handlers/github";
import { server } from "./mocks/server";

const AUTOMATIONS_URL = `${API_BASE_URL}/workspaces/ws-1/integrations/github/automations`;

function renderRules() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <GitHubAutomationRules workspaceId="ws-1" />
    </QueryClientProvider>,
  );
}

describe("GitHubAutomationRules", () => {
  it("shows the status chosen for each pull request situation", async () => {
    renderRules();

    expect(await screen.findByRole("combobox", { name: "PR aberto" })).toHaveTextContent("Todo");
    expect(screen.getByRole("combobox", { name: "PR mergeado" })).toHaveTextContent("Sem ação");
  });

  it("saves a new target and shows what the backend answered", async () => {
    const user = userEvent.setup();
    let saved: GitHubStatusAutomation | undefined;
    server.use(
      http.put(AUTOMATIONS_URL, async ({ request }) => {
        saved = (await request.json()) as GitHubStatusAutomation;
        return HttpResponse.json({
          data: demoGitHubAutomations.map((rule) => (rule.event === saved?.event ? saved : rule)),
        });
      }),
    );
    renderRules();

    await user.click(await screen.findByRole("combobox", { name: "PR mergeado" }));
    await user.click(await screen.findByRole("option", { name: "Todo" }));

    await waitFor(() =>
      expect(saved).toEqual({ event: "PR_MERGED", target_state_id: "workflow-state-todo" }),
    );
    expect(screen.getByRole("combobox", { name: "PR mergeado" })).toHaveTextContent("Todo");
  });

  it("clearing a rule sends null", async () => {
    const user = userEvent.setup();
    let saved: GitHubStatusAutomation | undefined;
    server.use(
      http.put(AUTOMATIONS_URL, async ({ request }) => {
        saved = (await request.json()) as GitHubStatusAutomation;
        return HttpResponse.json({ data: demoGitHubAutomations });
      }),
    );
    renderRules();

    await user.click(await screen.findByRole("combobox", { name: "PR aberto" }));
    await user.click(await screen.findByRole("option", { name: "Sem ação" }));

    await waitFor(() => expect(saved).toEqual({ event: "PR_OPEN", target_state_id: null }));
  });
});
