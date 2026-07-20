import { Link } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { IssuePriorityBadge } from "./IssuePriorityBadge";
import type { Issue } from "../types";

export function IssueBoardCard({
  workspaceSlug,
  issue,
  assigneeName,
}: {
  workspaceSlug: string;
  issue: Issue;
  assigneeName: string | undefined;
}) {
  return (
    <Link
      to={workspaceRoutes.issueDetail(workspaceSlug, issue.id)}
      className="flex flex-col gap-2 rounded-lg border bg-card p-3 text-sm hover:border-ring"
    >
      <p className="font-mono text-xs text-muted-foreground">{issue.identifier}</p>
      <p className="line-clamp-2 font-medium">{issue.title}</p>
      <div className="flex items-center justify-between">
        <IssuePriorityBadge priority={issue.priority} />
        {assigneeName && (
          <Avatar className="size-5">
            <AvatarFallback className="text-[10px]">{getInitials(assigneeName)}</AvatarFallback>
          </Avatar>
        )}
      </div>
    </Link>
  );
}
