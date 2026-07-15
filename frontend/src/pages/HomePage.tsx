import { Navigate } from "react-router-dom";

import { CreateFirstWorkspaceForm } from "@/features/workspaces/components/CreateFirstWorkspaceForm";
import { EmptyLayout } from "@/shared/components/layout/EmptyLayout";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { workspaceRoutes } from "@/shared/lib/routes";

export function HomePage() {
  const { data: profile, isLoading } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
    );
  }

  const firstWorkspace = profile?.workspaces[0];
  if (firstWorkspace) {
    return <Navigate to={workspaceRoutes.projects(firstWorkspace.slug)} replace />;
  }

  return (
    <EmptyLayout>
      <div>
        <h1 className="text-lg font-semibold">Crie seu primeiro workspace</h1>
        <p className="text-sm text-muted-foreground">
          Um workspace agrupa os projetos e times da sua organização.
        </p>
      </div>
      <CreateFirstWorkspaceForm />
    </EmptyLayout>
  );
}
