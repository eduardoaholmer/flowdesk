import { Badge } from "@/shared/components/ui/badge";

import type { IssueStatus } from "../types";

const LABELS: Record<IssueStatus, string> = {
  BACKLOG: "Backlog",
  TODO: "Todo",
  IN_PROGRESS: "In Progress",
  IN_REVIEW: "In Review",
  DONE: "Done",
  CANCELED: "Canceled",
};

const VARIANTS: Record<IssueStatus, "outline" | "secondary" | "default" | "destructive"> = {
  BACKLOG: "outline",
  TODO: "outline",
  IN_PROGRESS: "secondary",
  IN_REVIEW: "secondary",
  DONE: "default",
  CANCELED: "destructive",
};

export function IssueStatusBadge({ status }: { status: IssueStatus }) {
  return <Badge variant={VARIANTS[status]}>{LABELS[status]}</Badge>;
}
