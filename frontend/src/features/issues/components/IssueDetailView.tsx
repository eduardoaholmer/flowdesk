import { useNavigate } from "react-router-dom";

import { AttachmentList } from "@/features/attachments/components/AttachmentList";
import { CommentList } from "@/features/comments/components/CommentList";
import { IssueLabelPicker } from "@/features/labels/components/IssueLabelPicker";
import { useProjects } from "@/features/projects/hooks";
import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { Separator } from "@/shared/components/ui/separator";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";
import { formatDate } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";

import { useIssue } from "../hooks";
import { IssueActivityTimeline } from "./IssueActivityTimeline";
import { IssuePriorityBadge } from "./IssuePriorityBadge";
import { IssueRowActions } from "./IssueRowActions";
import { IssueStatusBadge } from "./IssueStatusBadge";

export function IssueDetailView({
  workspaceId,
  workspaceSlug,
  issueId,
}: {
  workspaceId: string;
  workspaceSlug: string;
  issueId: string;
}) {
  const navigate = useNavigate();
  const { data: issue, isLoading, isError, refetch } = useIssue(workspaceId, issueId);
  const { data: members } = useWorkspaceMembers(workspaceId);
  const { data: projects } = useProjects(workspaceId, {
    page: 1,
    per_page: MAX_PICKER_PAGE_SIZE,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full max-w-md" />
        <Skeleton className="h-4 w-full max-w-sm" />
      </div>
    );
  }

  if (isError || !issue) {
    return <ErrorState message="Issue não encontrada ou indisponível." onRetry={() => refetch()} />;
  }

  const assignee = members?.find((member) => member.user.id === issue.assignee_id)?.user;
  const project = projects?.data.find((p) => p.id === issue.project_id);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs text-muted-foreground">{issue.identifier}</p>
          <h1 className="text-lg font-semibold">{issue.title}</h1>
          <div className="mt-2 flex items-center gap-2">
            <IssueStatusBadge status={issue.status} />
            <IssuePriorityBadge priority={issue.priority} />
          </div>
          <div className="mt-2">
            <IssueLabelPicker workspaceId={workspaceId} issueId={issue.id} />
          </div>
        </div>
        <IssueRowActions
          workspaceId={workspaceId}
          issue={issue}
          onDeleted={() => navigate(workspaceRoutes.issues(workspaceSlug), { replace: true })}
        />
      </div>

      <div>
        <h2 className="mb-1 text-sm font-medium text-muted-foreground">Descrição</h2>
        <p className="text-sm whitespace-pre-wrap">{issue.description || "Sem descrição."}</p>
      </div>

      <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted-foreground">Responsável</dt>
          <dd>{assignee?.name ?? "Sem responsável"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Projeto</dt>
          <dd>{project?.name ?? "Sem projeto"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Estimativa</dt>
          <dd>{issue.estimate ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Vencimento</dt>
          <dd>{issue.due_date ? formatDate(issue.due_date) : "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Criado em</dt>
          <dd>{formatDate(issue.created_at)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Atualizado em</dt>
          <dd>{formatDate(issue.updated_at)}</dd>
        </div>
      </dl>

      <Separator />

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Anexos</h2>
        <AttachmentList workspaceId={workspaceId} issueId={issue.id} />
      </div>

      <Separator />

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Comentários</h2>
        <CommentList workspaceId={workspaceId} issueId={issue.id} />
      </div>

      <Separator />

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Atividade</h2>
        <IssueActivityTimeline workspaceId={workspaceId} issueId={issue.id} />
      </div>
    </div>
  );
}
