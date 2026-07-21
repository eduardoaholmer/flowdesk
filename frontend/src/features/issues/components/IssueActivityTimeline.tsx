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
    <ul className="flex flex-col gap-1">
      {entries.map((entry) => (
        <li key={entry.id} className="flex items-baseline gap-2.5 py-1 text-[12.5px] text-t2">
          <span className="relative top-[-1px] size-1.5 shrink-0 rounded-full bg-border2" />
          <span className="flex-1">
            <span className="font-semibold text-foreground">
              {ACTION_LABELS[entry.action] ?? entry.action}
            </span>
            {entry.field && (
              <span>
                {" "}
                — {entry.field}: {entry.old_value ?? "—"} → {entry.new_value ?? "—"}
              </span>
            )}
          </span>
          <span className="shrink-0 text-[11.5px] text-t3">{formatDateTime(entry.created_at)}</span>
        </li>
      ))}
    </ul>
  );
}
