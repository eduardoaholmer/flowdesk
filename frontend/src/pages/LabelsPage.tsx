import { Navigate } from "react-router-dom";

import { LabelsListPage } from "@/features/labels/components/LabelsListPage";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function LabelsPage() {
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace) {
    return <Navigate to="/" replace />;
  }

  return <LabelsListPage workspaceId={workspace.id} />;
}
