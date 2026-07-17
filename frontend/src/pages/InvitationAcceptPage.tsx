import { useEffect, useRef, useState } from "react";
import { Navigate, useParams } from "react-router-dom";

import { useAcceptInvitation } from "@/features/workspaces/hooks";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { EmptyLayout } from "@/shared/components/layout/EmptyLayout";
import { Spinner } from "@/shared/components/ui/spinner";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { getApiErrorMessage } from "@/shared/lib/errors";
import { workspaceRoutes } from "@/shared/lib/routes";

export function InvitationAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const acceptInvitation = useAcceptInvitation();
  const { data: profile, refetch: refetchProfile } = useCurrentUser();
  const [error, setError] = useState<string | null>(null);
  const attempted = useRef(false);

  useEffect(() => {
    if (!token || attempted.current) return;
    attempted.current = true;
    acceptInvitation.mutate(token, {
      onError: (err) => setError(getApiErrorMessage(err, "Não foi possível aceitar o convite.")),
      onSuccess: () => refetchProfile(),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (acceptInvitation.isSuccess) {
    const acceptedWorkspaceId = acceptInvitation.data.workspace_id;
    const workspace = profile?.workspaces.find((w) => w.id === acceptedWorkspaceId);
    if (workspace) {
      return <Navigate to={workspaceRoutes.issues(workspace.slug)} replace />;
    }
  }

  return (
    <EmptyLayout>
      {error ? (
        <ErrorState message={error} />
      ) : (
        <div className="flex flex-col items-center gap-3 text-center">
          <Spinner className="size-6" />
          <p className="text-sm text-muted-foreground">Aceitando convite…</p>
        </div>
      )}
    </EmptyLayout>
  );
}
