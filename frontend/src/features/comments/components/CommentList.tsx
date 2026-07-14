import { useState } from "react";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";

import { useComments } from "../hooks";
import { CommentComposer } from "./CommentComposer";
import { CommentItem } from "./CommentItem";

const PER_PAGE = 20;

export function CommentList({ workspaceId, issueId }: { workspaceId: string; issueId: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useComments(workspaceId, issueId, { page, per_page: PER_PAGE });
  const { data: members } = useWorkspaceMembers(workspaceId);
  const { data: currentUser } = useCurrentUser();

  function authorName(authorId: string): string {
    if (authorId === currentUser?.id) return "Você";
    return members?.find((member) => member.user.id === authorId)?.user.name ?? "Alguém";
  }

  return (
    <div className="flex flex-col gap-4">
      <CommentComposer workspaceId={workspaceId} issueId={issueId} />

      {isLoading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : !data || data.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhum comentário ainda.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {data.data.map((comment) => (
            <CommentItem
              key={comment.id}
              workspaceId={workspaceId}
              issueId={issueId}
              comment={comment}
              authorName={authorName(comment.author_id)}
              isOwnComment={comment.author_id === currentUser?.id}
            />
          ))}
          {data.meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-sm">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((prev) => prev - 1)}
              >
                Anterior
              </Button>
              <span className="text-muted-foreground">
                Página {page} de {data.meta.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= data.meta.total_pages}
                onClick={() => setPage((prev) => prev + 1)}
              >
                Próxima
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
