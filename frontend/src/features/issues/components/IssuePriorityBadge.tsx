import { AlertTriangle, ChevronDown, ChevronsDown, ChevronsUp, Minus } from "lucide-react";

import type { IssuePriority } from "../types";

const LABELS: Record<IssuePriority, string> = {
  NO_PRIORITY: "No priority",
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  URGENT: "Urgent",
};

const ICONS: Record<IssuePriority, React.ComponentType<{ className?: string }>> = {
  NO_PRIORITY: Minus,
  LOW: ChevronsDown,
  MEDIUM: ChevronDown,
  HIGH: ChevronsUp,
  URGENT: AlertTriangle,
};

export function IssuePriorityBadge({ priority }: { priority: IssuePriority }) {
  const Icon = ICONS[priority];
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
      <Icon className="size-3.5" />
      {LABELS[priority]}
    </span>
  );
}
