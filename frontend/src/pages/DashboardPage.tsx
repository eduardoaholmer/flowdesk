import { Navigate } from "react-router-dom";

import { DashboardView } from "@/features/dashboard/components/DashboardView";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";

export function DashboardPage() {
  const { workspace, isLoading: isWorkspaceLoading } = useWorkspace();
  const { data: profile, isLoading: isProfileLoading } = useCurrentUser();

  if (isWorkspaceLoading || isProfileLoading) {
    return <Skeleton className="h-8 w-48" />;
  }
  if (!workspace || !profile) {
    return <Navigate to="/" replace />;
  }

  return (
    <DashboardView
      workspaceId={workspace.id}
      workspaceSlug={workspace.slug}
      workspaceName={workspace.name}
      userId={profile.id}
      userName={profile.name}
    />
  );
}
