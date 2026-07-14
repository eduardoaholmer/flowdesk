import { Navigate, useParams } from "react-router-dom";

import { IssueDetailView } from "@/features/issues/components/IssueDetailView";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function IssueDetailPage() {
  const { issueId } = useParams<{ issueId: string }>();
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace || !issueId) {
    return <Navigate to="/" replace />;
  }

  return (
    <IssueDetailView workspaceId={workspace.id} workspaceSlug={workspace.slug} issueId={issueId} />
  );
}
