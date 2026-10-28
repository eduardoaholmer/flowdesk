import {
  GitMerge,
  GitPullRequest,
  GitPullRequestClosed,
  GitPullRequestDraft,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/shared/lib/utils";

import { useIssueGitHubLinks } from "../hooks";
import type { GitHubPullRequestState } from "../types";

const STATE_PRESENTATION: Record<
  GitHubPullRequestState,
  { icon: LucideIcon; label: string; className: string }
> = {
  OPEN: { icon: GitPullRequest, label: "Aberto", className: "text-green" },
  DRAFT: { icon: GitPullRequestDraft, label: "Rascunho", className: "text-t3" },
  MERGED: { icon: GitMerge, label: "Mergeado", className: "text-foreground" },
  CLOSED: { icon: GitPullRequestClosed, label: "Fechado", className: "text-destructive" },
};

/** Seção "Pull requests" do rail da issue. Some quando nenhum PR cita a issue: num
 * workspace sem GitHub conectado ela seria só ruído. */
export function IssuePullRequests({
  workspaceId,
  issueId,
}: {
  workspaceId: string;
  issueId: string;
}) {
  const { data: links } = useIssueGitHubLinks(workspaceId, issueId);

  if (!links || links.length === 0) return null;

  return (
    <div>
      <div className="mb-1.5 text-[10.5px] font-semibold tracking-wide text-t3 uppercase">
        Pull requests
      </div>
      <ul className="flex flex-col gap-2">
        {links.map((link) => {
          const state = STATE_PRESENTATION[link.pr_state];
          const Icon = state.icon;
          return (
            <li key={link.id} className="flex items-start gap-2">
              <Icon
                className={cn("mt-0.5 size-4 shrink-0", state.className)}
                aria-label={state.label}
                role="img"
              />
              <div className="min-w-0 text-[12.5px] leading-snug">
                <a
                  href={link.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium hover:underline"
                >
                  {link.pr_title}
                </a>
                <p className="truncate text-[11.5px] text-t3">
                  {link.repository_full_name}#{link.pr_number} · {link.author_login}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
