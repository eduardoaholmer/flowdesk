import { Mail } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { Pagination } from "@/shared/components/navigation/Pagination";
import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Dialog, DialogContent } from "@/shared/components/ui/dialog";
import { TableSkeleton } from "@/shared/components/skeletons/TableSkeleton";
import { formatDate } from "@/shared/lib/date";
import { cn } from "@/shared/lib/utils";

import { useCancelInvitation, useInvitations, useResendInvitation } from "../hooks";
import type { Invitation, InvitationCreatedResult } from "../types";
import { InviteLinkStep } from "./InviteLinkStep";
import { InviteMemberDialog } from "./InviteMemberDialog";

const PER_PAGE = 20;

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
  const resendInvitation = useResendInvitation(workspaceId);
  const [resent, setResent] = useState<InvitationCreatedResult | null>(null);

  const canResend = invitation.status === "PENDING" || invitation.status === "EXPIRED";

  return (
    <>
      <div className="flex items-center gap-3 border-b py-3 last:border-b-0">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{invitation.email}</p>
          <p className="text-xs text-muted-foreground">
            Expira em {formatDate(invitation.expires_at)}
          </p>
        </div>
        <Badge variant="outline">{invitation.role}</Badge>
        <Badge variant={statusVariant(invitation.status)}>{invitation.status}</Badge>
        {canResend && (
          <Button
            variant="ghost"
            size="sm"
            disabled={resendInvitation.isPending}
            onClick={() =>
              resendInvitation.mutate(invitation.id, { onSuccess: (result) => setResent(result) })
            }
          >
            Reenviar
          </Button>
        )}
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
      <Dialog open={resent !== null} onOpenChange={(next) => !next && setResent(null)}>
        <DialogContent>
          {resent && <InviteLinkStep invitation={resent} onDone={() => setResent(null)} />}
        </DialogContent>
      </Dialog>
    </>
  );
}

export function WorkspaceInvitationsSettings({ workspaceId }: { workspaceId: string }) {
  const [page, setPage] = useState(1);
  const {
    data: invitations,
    isLoading,
    isError,
    refetch,
    isPlaceholderData,
  } = useInvitations(workspaceId, { page, per_page: PER_PAGE });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-heading text-lg font-semibold tracking-tight">Convites</h2>
          <p className="text-sm text-t2">
            Convites pendentes, aceitos e expirados deste workspace.
          </p>
        </div>
        <InviteMemberDialog workspaceId={workspaceId} />
      </div>

      {isLoading ? (
        <TableSkeleton rows={3} />
      ) : isError ? (
        <ErrorState message="Não foi possível carregar os convites." onRetry={() => refetch()} />
      ) : invitations && invitations.data.length > 0 ? (
        <div className={cn("flex flex-col gap-4", isPlaceholderData && "opacity-60")}>
          <div className="rounded-xl border border-border bg-panel px-4">
            {invitations.data.map((invitation) => (
              <InvitationRow
                key={invitation.id}
                invitation={invitation}
                workspaceId={workspaceId}
              />
            ))}
          </div>
          <Pagination meta={invitations.meta} itemLabel="convite" onPageChange={setPage} />
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
