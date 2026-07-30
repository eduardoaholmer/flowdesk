import { ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { AttachmentList } from "@/features/attachments/components/AttachmentList";
import { CommentList } from "@/features/comments/components/CommentList";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Button } from "@/shared/components/ui/button";
import { Separator } from "@/shared/components/ui/separator";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { workspaceRoutes } from "@/shared/lib/routes";
import { useUiStore } from "@/shared/stores/uiStore";

import { useIssue, useIssues } from "../hooks";
import { IssueActivityTimeline } from "./IssueActivityTimeline";
import { IssueDetailRail } from "./IssueDetailRail";
import { IssueRowActions } from "./IssueRowActions";
import { IssuesEmptyState } from "./IssuesEmptyState";
import { IssuesTable } from "./IssuesTable";

const SECTION_HEADING = "mb-3 text-[11px] font-semibold tracking-wide text-t3 uppercase";

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
  const setCreateIssueParentId = useUiStore((state) => state.setCreateIssueParentId);
  const setCreateIssueOpen = useUiStore((state) => state.setCreateIssueOpen);
  const subIssuesQuery = useIssues(workspaceId, {
    page: 1,
    per_page: 20,
    parent_id: issueId,
    sort: "-updated_at",
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

  return (
    <div className="flex flex-col items-start gap-8 md:flex-row">
      <div className="w-full min-w-0 md:max-w-3xl">
        <Link
          to={workspaceRoutes.issues(workspaceSlug)}
          className="mb-4 inline-flex items-center gap-1.5 text-xs text-t3 hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          Issues
        </Link>

        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="mb-1 text-xs text-t3">{issue.identifier}</p>
            <h1 className="font-heading text-2xl leading-tight font-semibold">{issue.title}</h1>
          </div>
          <IssueRowActions
            workspaceId={workspaceId}
            issue={issue}
            onDeleted={() => navigate(workspaceRoutes.issues(workspaceSlug), { replace: true })}
          />
        </div>

        <p className="mt-5 text-sm leading-relaxed whitespace-pre-wrap text-t2">
          {issue.description || "Sem descrição."}
        </p>

        <Separator className="my-6" />

        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className={SECTION_HEADING}>
              Sub-issues
              {subIssuesQuery.data && subIssuesQuery.data.meta.total > 0 && (
                <span className="ml-1.5 normal-case">({subIssuesQuery.data.meta.total})</span>
              )}
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCreateIssueParentId(issue.id);
                setCreateIssueOpen(true);
              }}
            >
              Nova sub-issue
            </Button>
          </div>
          {subIssuesQuery.isLoading ? (
            <ListSkeleton rows={3} />
          ) : subIssuesQuery.isError ? (
            <ErrorState
              message="Não foi possível carregar as sub-issues."
              onRetry={() => subIssuesQuery.refetch()}
            />
          ) : subIssuesQuery.data && subIssuesQuery.data.data.length > 0 ? (
            <IssuesTable
              workspaceId={workspaceId}
              workspaceSlug={workspaceSlug}
              issues={subIssuesQuery.data.data}
              showProject={false}
            />
          ) : (
            <IssuesEmptyState hasFilters={false} />
          )}
        </div>

        <Separator className="my-6" />

        <div>
          <h2 className={SECTION_HEADING}>Anexos</h2>
          <AttachmentList workspaceId={workspaceId} issueId={issue.id} />
        </div>

        <Separator className="my-6" />

        <div>
          <h2 className={SECTION_HEADING}>Atividade</h2>
          <IssueActivityTimeline workspaceId={workspaceId} issueId={issue.id} />
        </div>

        <Separator className="my-6" />

        <div>
          <h2 className={SECTION_HEADING}>Comentários</h2>
          <CommentList workspaceId={workspaceId} issueId={issue.id} />
        </div>
      </div>

      <IssueDetailRail workspaceId={workspaceId} issue={issue} />
    </div>
  );
}
