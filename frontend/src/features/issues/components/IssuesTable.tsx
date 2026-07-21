import { Link } from "react-router-dom";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { formatDate, formatRelativeTime } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { ISSUE_PRIORITY_LABELS, ISSUE_STATUS_LABELS } from "../constants";
import { IssuePriorityIcon } from "./IssuePriorityIcon";
import { IssueRowActions } from "./IssueRowActions";
import { IssueStatusIcon } from "./IssueStatusIcon";
import type { Issue } from "../types";

export function IssuesTable({
  workspaceId,
  workspaceSlug,
  issues,
}: {
  workspaceId: string;
  workspaceSlug: string;
  issues: Issue[];
}) {
  const { data: members } = useWorkspaceMembers(workspaceId);
  const memberById = new Map((members ?? []).map((member) => [member.user.id, member.user]));

  return (
    <div className="rounded-xl border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-20">Id</TableHead>
            <TableHead>Título</TableHead>
            <TableHead className="w-10">Status</TableHead>
            <TableHead className="w-10">Prioridade</TableHead>
            <TableHead>Responsável</TableHead>
            <TableHead>Vencimento</TableHead>
            <TableHead>Atualizado</TableHead>
            <TableHead className="w-24 text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {issues.map((issue) => {
            const assignee = issue.assignee_id ? memberById.get(issue.assignee_id) : undefined;
            return (
              <TableRow key={issue.id}>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {issue.identifier}
                </TableCell>
                <TableCell>
                  <Link
                    to={workspaceRoutes.issueDetail(workspaceSlug, issue.id)}
                    className="font-medium hover:underline"
                  >
                    {issue.title}
                  </Link>
                </TableCell>
                <TableCell>
                  <span
                    role="img"
                    aria-label={ISSUE_STATUS_LABELS[issue.status]}
                    title={ISSUE_STATUS_LABELS[issue.status]}
                    className="inline-flex"
                  >
                    <IssueStatusIcon status={issue.status} />
                  </span>
                </TableCell>
                <TableCell>
                  <span
                    role="img"
                    aria-label={ISSUE_PRIORITY_LABELS[issue.priority]}
                    title={ISSUE_PRIORITY_LABELS[issue.priority]}
                    className="inline-flex"
                  >
                    <IssuePriorityIcon priority={issue.priority} />
                  </span>
                </TableCell>
                <TableCell>
                  {assignee ? (
                    <div className="flex items-center gap-2">
                      <Avatar className="size-5">
                        <AvatarFallback className="text-[10px]">
                          {getInitials(assignee.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm">{assignee.name}</span>
                    </div>
                  ) : (
                    <span className="text-sm text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {issue.due_date ? formatDate(issue.due_date) : "—"}
                </TableCell>
                <TableCell className="text-sm text-t3">
                  {formatRelativeTime(issue.updated_at)}
                </TableCell>
                <TableCell>
                  <div className="flex justify-end">
                    <IssueRowActions workspaceId={workspaceId} issue={issue} />
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
