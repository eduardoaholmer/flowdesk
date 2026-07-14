import { Navigate } from "react-router-dom";

import { CreateFirstWorkspaceForm } from "@/features/workspaces/components/CreateFirstWorkspaceForm";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { Skeleton } from "@/shared/components/ui/skeleton";

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
    return <Navigate to={`/w/${firstWorkspace.slug}/projects`} replace />;
  }

  return (
    <div className="mx-auto flex max-w-sm flex-col gap-4 pt-12">
      <div>
        <h1 className="text-lg font-semibold">Crie seu primeiro workspace</h1>
        <p className="text-sm text-muted-foreground">
          Um workspace agrupa os projetos e times da sua organização.
        </p>
      </div>
      <CreateFirstWorkspaceForm />
    </div>
  );
}
