import { ArrowLeft, ChevronDown, ChevronUp, X } from "lucide-react";
import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import { AttachmentList } from "@/features/attachments/components/AttachmentList";
import { CommentList } from "@/features/comments/components/CommentList";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Button } from "@/shared/components/ui/button";
import { Separator } from "@/shared/components/ui/separator";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { isTypingTarget } from "@/shared/lib/dom";
import { workspaceRoutes } from "@/shared/lib/routes";
import { cn } from "@/shared/lib/utils";
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
  onClose,
  onNavigate,
  hasPrevious,
  hasNext,
}: {
  workspaceId: string;
  workspaceSlug: string;
  issueId: string;
  /** Modo painel lateral (Sprint 9.5, `IssuesListPage`): substitui o link
   * "Voltar para Issues" por um botão de fechar, e excluir a issue fecha o
   * painel em vez de navegar para longe da lista. */
  onClose?: () => void;
  onNavigate?: (direction: "previous" | "next") => void;
  hasPrevious?: boolean;
  hasNext?: boolean;
}) {
  const navigate = useNavigate();
  const { data: issue, isLoading, isError, refetch } = useIssue(workspaceId, issueId);

  // Atalhos de teclado J/K (navegar) — só faz sentido no painel lateral, onde
  // existe uma lista ordenada por trás; a página cheia (link direto/compartilhado)
  // não tem esse contexto, então `onNavigate` nunca é passado ali.
  useEffect(() => {
    if (!onNavigate) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey || isTypingTarget(event.target)) return;
      if (event.key === "j" || event.key === "ArrowDown") {
        event.preventDefault();
        onNavigate?.("next");
      } else if (event.key === "k" || event.key === "ArrowUp") {
        event.preventDefault();
        onNavigate?.("previous");
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onNavigate]);
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

  // No painel lateral (`onClose` presente), a largura já é fixa e estreita
  // (`IssuesListPage`) — empilhar conteúdo+rail sempre, ignorando os
  // breakpoints `md:` pensados para a página cheia, que assumem a largura
  // real da viewport, não a do painel.
  return (
    <div className={cn("flex flex-col items-start gap-8", !onClose && "md:flex-row")}>
      <div className={cn("w-full min-w-0", !onClose && "md:max-w-3xl")}>
        <div className="mb-4 flex items-center justify-between gap-2">
          {onClose ? (
            <>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Issue anterior"
                  disabled={!hasPrevious}
                  onClick={() => onNavigate?.("previous")}
                >
                  <ChevronUp />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Próxima issue"
                  disabled={!hasNext}
                  onClick={() => onNavigate?.("next")}
                >
                  <ChevronDown />
                </Button>
              </div>
              <Button variant="ghost" size="icon-sm" aria-label="Fechar painel" onClick={onClose}>
                <X />
              </Button>
            </>
          ) : (
            <Link
              to={workspaceRoutes.issues(workspaceSlug)}
              className="inline-flex items-center gap-1.5 text-xs text-t3 hover:text-foreground"
            >
              <ArrowLeft className="size-3.5" />
              Issues
            </Link>
          )}
        </div>

        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="mb-1 text-xs text-t3">{issue.identifier}</p>
            <h1 className="font-heading text-2xl leading-tight font-semibold">{issue.title}</h1>
          </div>
          <IssueRowActions
            workspaceId={workspaceId}
            issue={issue}
            onDeleted={() =>
              onClose
                ? onClose()
                : navigate(workspaceRoutes.issues(workspaceSlug), { replace: true })
            }
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

      <IssueDetailRail workspaceId={workspaceId} issue={issue} isPanel={Boolean(onClose)} />
    </div>
  );
}
