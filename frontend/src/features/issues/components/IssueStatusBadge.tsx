import { Badge } from "@/shared/components/ui/badge";

import { ISSUE_STATUS_LABELS } from "../constants";
import type { IssueStatus } from "../types";

const VARIANTS: Record<IssueStatus, "outline" | "secondary" | "default" | "destructive"> = {
  BACKLOG: "outline",
  TODO: "outline",
  IN_PROGRESS: "secondary",
  IN_REVIEW: "secondary",
  DONE: "default",
  CANCELED: "destructive",
};

export function IssueStatusBadge({ status }: { status: IssueStatus }) {
  return <Badge variant={VARIANTS[status]}>{ISSUE_STATUS_LABELS[status]}</Badge>;
}
