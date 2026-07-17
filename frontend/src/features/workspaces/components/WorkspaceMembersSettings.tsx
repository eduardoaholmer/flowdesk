import { Users } from "lucide-react";

import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { TableSkeleton } from "@/shared/components/skeletons/TableSkeleton";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { formatDate } from "@/shared/lib/date";
import { getInitials } from "@/shared/lib/string";

import {
  useLeaveWorkspace,
  useRemoveMember,
  useUpdateMemberRole,
  useWorkspaceMembers,
} from "../hooks";
import type { WorkspaceMember, WorkspaceRole } from "../types";
import { InviteMemberDialog } from "./InviteMemberDialog";

const MANAGEABLE_ROLES: Exclude<WorkspaceRole, "OWNER">[] = ["ADMIN", "MEMBER", "GUEST"];

function MemberRow({
  member,
  workspaceId,
  isSelf,
  canManage,
}: {
  member: WorkspaceMember;
  workspaceId: string;
  isSelf: boolean;
  canManage: boolean;
}) {
  const updateRole = useUpdateMemberRole(workspaceId);
  const removeMember = useRemoveMember(workspaceId);
  const leaveWorkspace = useLeaveWorkspace();

  const canManageThisMember = canManage && !isSelf && member.role !== "OWNER";

  return (
    <div className="flex items-center gap-3 border-b py-3 last:border-b-0">
      <Avatar size="sm">
        <AvatarFallback>{getInitials(member.user.name)}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">
          {member.user.name} {isSelf && <span className="text-muted-foreground">(você)</span>}
        </p>
        <p className="truncate text-xs text-muted-foreground">{member.user.email}</p>
      </div>
      <span className="hidden text-xs text-muted-foreground sm:inline">
        Desde {formatDate(member.joined_at)}
      </span>

      {canManageThisMember ? (
        <Select
          value={member.role}
          onValueChange={(role) =>
            updateRole.mutate({ memberId: member.id, role: role as WorkspaceRole })
          }
        >
          <SelectTrigger size="sm" className="w-28">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {MANAGEABLE_ROLES.map((role) => (
              <SelectItem key={role} value={role}>
                {role}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <Badge variant={member.role === "OWNER" ? "default" : "outline"}>{member.role}</Badge>
      )}

      {isSelf
        ? member.role !== "OWNER" && (
            <ConfirmActionDialog
              trigger={
                <Button variant="ghost" size="sm">
                  Sair
                </Button>
              }
              title="Sair deste workspace?"
              description="Você perderá acesso a todos os projetos e issues deste workspace."
              confirmLabel="Sair"
              destructive
              isPending={leaveWorkspace.isPending}
              onConfirm={() => leaveWorkspace.mutate(workspaceId)}
            />
          )
        : canManageThisMember && (
            <ConfirmActionDialog
              trigger={
                <Button variant="ghost" size="sm" className="text-destructive">
                  Remover
                </Button>
              }
              title="Remover este membro?"
              description={`${member.user.name} perderá acesso a este workspace.`}
              confirmLabel="Remover"
              destructive
              isPending={removeMember.isPending}
              onConfirm={() => removeMember.mutate(member.id)}
            />
          )}
    </div>
  );
}

export function WorkspaceMembersSettings({
  workspaceId,
  canManage,
}: {
  workspaceId: string;
  canManage: boolean;
}) {
  const { data: profile } = useCurrentUser();
  const { data: members, isLoading, isError, refetch } = useWorkspaceMembers(workspaceId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-medium">Membros</h2>
          <p className="text-sm text-muted-foreground">
            Gerencie quem tem acesso a este workspace e seus papéis.
          </p>
        </div>
        {canManage && <InviteMemberDialog workspaceId={workspaceId} />}
      </div>

      {isLoading ? (
        <TableSkeleton rows={4} />
      ) : isError ? (
        <ErrorState message="Não foi possível carregar os membros." onRetry={() => refetch()} />
      ) : members && members.length > 0 ? (
        <div className="rounded-lg border px-4">
          {members.map((member) => (
            <MemberRow
              key={member.id}
              member={member}
              workspaceId={workspaceId}
              isSelf={member.user.id === profile?.id}
              canManage={canManage}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Users}
          title="Nenhum membro"
          description="Este workspace não tem membros."
        />
      )}
    </div>
  );
}
