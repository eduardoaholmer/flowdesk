import { Navigate } from "react-router-dom";

import { IssuesBoardView } from "@/features/issues/components/IssuesBoardView";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function BoardPage() {
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace) {
    return <Navigate to="/" replace />;
  }

  return <IssuesBoardView workspaceId={workspace.id} workspaceSlug={workspace.slug} />;
}
