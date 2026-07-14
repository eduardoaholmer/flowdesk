import { Navigate, useParams } from "react-router-dom";

import { ProjectDetailView } from "@/features/projects/components/ProjectDetailView";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace || !projectId) {
    return <Navigate to="/" replace />;
  }

  return (
    <ProjectDetailView
      workspaceId={workspace.id}
      workspaceSlug={workspace.slug}
      projectId={projectId}
    />
  );
}
