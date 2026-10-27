import type { WorkflowState } from "@/features/workflow-states/types";

import { IssueStatusIcon } from "./IssueStatusIcon";

export function IssueStatusBadge({ workflowState }: { workflowState: WorkflowState }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <IssueStatusIcon category={workflowState.category} />
      {workflowState.name}
    </span>
  );
}
