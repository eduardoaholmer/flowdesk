import { ISSUE_STATUS_LABELS } from "../constants";
import type { IssueStatus } from "../types";
import { IssueStatusIcon } from "./IssueStatusIcon";

export function IssueStatusBadge({ status }: { status: IssueStatus }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <IssueStatusIcon status={status} />
      {ISSUE_STATUS_LABELS[status]}
    </span>
  );
}
