import { Navigate } from "react-router-dom";

import { ProjectsListPage } from "@/features/projects/components/ProjectsListPage";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function ProjectsPage() {
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace) {
    return <Navigate to="/" replace />;
  }

  return <ProjectsListPage workspaceId={workspace.id} workspaceSlug={workspace.slug} />;
}
