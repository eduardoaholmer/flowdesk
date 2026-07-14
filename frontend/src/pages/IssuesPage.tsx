import { Navigate } from "react-router-dom";

import { IssuesListPage } from "@/features/issues/components/IssuesListPage";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function IssuesPage() {
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace) {
    return <Navigate to="/" replace />;
  }

  return <IssuesListPage workspaceId={workspace.id} workspaceSlug={workspace.slug} />;
}
