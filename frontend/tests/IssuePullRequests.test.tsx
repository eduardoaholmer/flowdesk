import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { IssuePullRequests } from "@/features/github/components/IssuePullRequests";
import type { GitHubPullRequestLink } from "@/features/github/types";

import { API_BASE_URL } from "./mocks/apiBaseUrl";
import { server } from "./mocks/server";

const LINKS_URL = `${API_BASE_URL}/workspaces/ws-1/issues/issue-1/github-links`;

const mergedLink: GitHubPullRequestLink = {
  id: "link-1",
  repository_full_name: "acme/api",
  pr_number: 42,
  pr_url: "https://github.com/acme/api/pull/42",
  pr_title: "Corrige login no Safari",
  pr_state: "MERGED",
  author_login: "ada",
  head_branch: "fd-1-corrige-login",
  pr_updated_at: "2026-10-27T12:00:00Z",
};

function renderSection() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <IssuePullRequests workspaceId="ws-1" issueId="issue-1" />
    </QueryClientProvider>,
  );
}

describe("IssuePullRequests", () => {
  it("lists the pull requests citing the issue, linking to GitHub", async () => {
    server.use(http.get(LINKS_URL, () => HttpResponse.json({ data: [mergedLink] })));

    renderSection();

    const link = await screen.findByRole("link", { name: "Corrige login no Safari" });
    expect(link).toHaveAttribute("href", "https://github.com/acme/api/pull/42");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByText("acme/api#42 · ada")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Mergeado" })).toBeInTheDocument();
  });

  it("renders nothing when no pull request cites the issue", async () => {
    let requested = false;
    server.use(
      http.get(LINKS_URL, () => {
        requested = true;
        return HttpResponse.json({ data: [] });
      }),
    );

    const { container } = renderSection();

    await waitFor(() => expect(requested).toBe(true));
    expect(container).toBeEmptyDOMElement();
  });
});
