import { Mail } from "lucide-react";

import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { TableSkeleton } from "@/shared/components/skeletons/TableSkeleton";
import { formatDate } from "@/shared/lib/date";

import { useCancelInvitation, useInvitations } from "../hooks";
import type { Invitation } from "../types";
import { InviteMemberDialog } from "./InviteMemberDialog";

function statusVariant(status: Invitation["status"]) {
  if (status === "PENDING") return "outline" as const;
  if (status === "ACCEPTED") return "default" as const;
  return "secondary" as const;
}

function InvitationRow({
  invitation,
  workspaceId,
}: {
  invitation: Invitation;
  workspaceId: string;
}) {
  const cancelInvitation = useCancelInvitation(workspaceId);

  return (
    <div className="flex items-center gap-3 border-b py-3 last:border-b-0">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{invitation.email}</p>
        <p className="text-xs text-muted-foreground">
          Expira em {formatDate(invitation.expires_at)}
        </p>
      </div>
      <Badge variant="outline">{invitation.role}</Badge>
      <Badge variant={statusVariant(invitation.status)}>{invitation.status}</Badge>
      {invitation.status === "PENDING" && (
        <ConfirmActionDialog
          trigger={
            <Button variant="ghost" size="sm" className="text-destructive">
              Cancelar
            </Button>
          }
          title="Cancelar este convite?"
          description={`O link enviado para ${invitation.email} deixará de funcionar.`}
          confirmLabel="Cancelar convite"
          destructive
          isPending={cancelInvitation.isPending}
          onConfirm={() => cancelInvitation.mutate(invitation.id)}
        />
      )}
    </div>
  );
}

export function WorkspaceInvitationsSettings({ workspaceId }: { workspaceId: string }) {
  const { data: invitations, isLoading, isError, refetch } = useInvitations(workspaceId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-medium">Convites</h2>
          <p className="text-sm text-muted-foreground">
            Convites pendentes, aceitos e expirados deste workspace.
          </p>
        </div>
        <InviteMemberDialog workspaceId={workspaceId} />
      </div>

      {isLoading ? (
        <TableSkeleton rows={3} />
      ) : isError ? (
        <ErrorState message="Não foi possível carregar os convites." onRetry={() => refetch()} />
      ) : invitations && invitations.length > 0 ? (
        <div className="rounded-lg border px-4">
          {invitations.map((invitation) => (
            <InvitationRow key={invitation.id} invitation={invitation} workspaceId={workspaceId} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Mail}
          title="Nenhum convite ainda"
          description="Convide alguém para este workspace."
        />
      )}
    </div>
  );
}
