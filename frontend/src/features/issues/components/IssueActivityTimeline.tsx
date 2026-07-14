import { Skeleton } from "@/shared/components/ui/skeleton";
import { formatDateTime } from "@/shared/lib/date";

import { useIssueActivity } from "../hooks";

const ACTION_LABELS: Record<string, string> = {
  "issue.created": "Issue criada",
  "issue.updated": "Issue atualizada",
  "issue.status_changed": "Status alterado",
  "issue.priority_changed": "Prioridade alterada",
  "issue.assignee_changed": "Responsável alterado",
  "issue.deleted": "Issue excluída",
};

export function IssueActivityTimeline({
  workspaceId,
  issueId,
}: {
  workspaceId: string;
  issueId: string;
}) {
  const { data: entries, isLoading } = useIssueActivity(workspaceId, issueId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="h-4 w-full max-w-sm" />
        <Skeleton className="h-4 w-full max-w-xs" />
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return <p className="text-sm text-muted-foreground">Nenhuma atividade registrada.</p>;
  }

  return (
    <ul className="flex flex-col gap-3">
      {entries.map((entry) => (
        <li key={entry.id} className="border-l-2 pl-3 text-sm">
          <span className="font-medium">{ACTION_LABELS[entry.action] ?? entry.action}</span>
          {entry.field && (
            <span className="text-muted-foreground">
              {" "}
              — {entry.field}: {entry.old_value ?? "—"} → {entry.new_value ?? "—"}
            </span>
          )}
          <div className="text-xs text-muted-foreground">{formatDateTime(entry.created_at)}</div>
        </li>
      ))}
    </ul>
  );
}
