import { Navigate } from "react-router-dom";

import { WorkspaceSettingsPage as WorkspaceSettingsView } from "@/features/workspaces/components/WorkspaceSettingsPage";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function WorkspaceSettingsPage() {
  const { workspace, isLoading } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace) {
    return <Navigate to="/" replace />;
  }

  return <WorkspaceSettingsView workspaceId={workspace.id} role={workspace.role} />;
}
