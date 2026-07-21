import { ISSUE_PRIORITY_LABELS } from "../constants";
import type { IssuePriority } from "../types";
import { IssuePriorityIcon } from "./IssuePriorityIcon";

export function IssuePriorityBadge({ priority }: { priority: IssuePriority }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
      <IssuePriorityIcon priority={priority} />
      {ISSUE_PRIORITY_LABELS[priority]}
    </span>
  );
}
