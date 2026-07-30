import { Badge } from "@/shared/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";

import { WORKFLOW_STATE_CATEGORY_LABELS } from "../constants";
import type { WorkflowState } from "../types";
import { IssueStatusIcon } from "@/features/issues/components/IssueStatusIcon";
import { WorkflowStateRowActions } from "./WorkflowStateRowActions";

export function WorkflowStatesTable({
  workspaceId,
  workflowStates,
}: {
  workspaceId: string;
  workflowStates: WorkflowState[];
}) {
  return (
    <div className="rounded-xl border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Status</TableHead>
            <TableHead>Categoria</TableHead>
            <TableHead className="w-24 text-right">Uso</TableHead>
            <TableHead className="w-36 text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {workflowStates.map((state, index) => (
            <TableRow key={state.id}>
              <TableCell>
                <span className="inline-flex items-center gap-1.5 text-sm font-medium">
                  <IssueStatusIcon category={state.category} />
                  {state.name}
                  {state.is_default && <Badge variant="secondary">Padrão</Badge>}
                </span>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {WORKFLOW_STATE_CATEGORY_LABELS[state.category]}
              </TableCell>
              <TableCell className="text-right text-muted-foreground">
                {state.issue_count} {state.issue_count === 1 ? "issue" : "issues"}
              </TableCell>
              <TableCell>
                <div className="flex justify-end">
                  <WorkflowStateRowActions
                    workspaceId={workspaceId}
                    workflowState={state}
                    allStates={workflowStates}
                    index={index}
                  />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
